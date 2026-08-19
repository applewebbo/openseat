from django.contrib.auth.decorators import login_not_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from events.forms import IdentifyForm
from events.models import Booking, Event
from intake.models import PublicForm, SectionKey, Submission
from members.models import Member

CONTACT_SESSION_KEY = "events_contact"


def _open_event(slug):
    return get_object_or_404(Event, slug=slug, is_published=True)


def _household(request, event):
    """Everyone the visitor has proven they may book for, or nobody."""
    email = request.session.get(CONTACT_SESSION_KEY)
    if not email:
        return Member.objects.none()
    return Member.objects.for_contact(event.association, email)


@login_not_required
def landing(request, slug):
    """The event, and the two ways in: already a member, or not yet."""
    event = _open_event(slug)
    return render(
        request,
        "events/landing.html",
        {
            "event": event,
            "association": event.association,
            "form": IdentifyForm(association=event.association),
        },
    )


@login_not_required
@require_POST
def identify(request, slug):
    event = _open_event(slug)
    form = IdentifyForm(data=request.POST, association=event.association)
    if not form.is_valid():
        return render(
            request,
            "events/landing.html",
            {"event": event, "association": event.association, "form": form},
        )

    request.session[CONTACT_SESSION_KEY] = form.cleaned_data["email"]
    return redirect("events:book", slug=event.slug)


@login_not_required
def book(request, slug):
    """Tick who is coming. Unticking somebody cancels their place."""
    event = _open_event(slug)
    household = _household(request, event)
    if not household.exists():
        return redirect("events:landing", slug=event.slug)

    if request.method == "POST":
        if not event.is_open:
            # The clock, not capacity, is the only thing that closes bookings.
            raise Http404("bookings are closed")
        chosen = household.filter(pk__in=request.POST.getlist("members"))
        if chosen.exists():
            for member in chosen:
                Booking.objects.book(event, member)
            for booking in (
                event.bookings.confirmed()
                .exclude(member__in=chosen)
                .filter(member__in=household)
            ):
                booking.cancel()
            return redirect("events:booked", slug=event.slug)

    return render(
        request,
        "events/book.html",
        {
            "event": event,
            "association": event.association,
            "members": household,
            "booked": set(
                event.bookings.confirmed().values_list("member_id", flat=True)
            ),
            "nobody_chosen": request.method == "POST",
        },
    )


@login_not_required
def booked(request, slug):
    event = _open_event(slug)
    household = _household(request, event)
    return render(
        request,
        "events/booked.html",
        {
            "event": event,
            "association": event.association,
            "bookings": event.bookings.confirmed().filter(member__in=household),
        },
    )


@login_not_required
@require_POST
def join(request, slug):
    """Not on the register yet: joining is how you book, by the current statute."""
    event = _open_event(slug)
    # An association may hold more than one public form — last year's application
    # left open, a form for a specific project — so the newest open one is the
    # application in use rather than "the" one. Meta.ordering makes that first().
    public_form = PublicForm.objects.filter(
        association=event.association, is_open=True
    ).first()
    if public_form is None:
        raise Http404("this association has no open application form")
    submission = Submission.objects.create(form=public_form, event=event)
    request.session["intake_draft"] = str(submission.token)
    return redirect("intake:step", token=submission.token, step=SectionKey.SUBJECT)
