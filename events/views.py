from django.contrib.auth.decorators import login_not_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from events.access import email_from_token
from events.forms import BookingContactForm, IdentifyForm
from events.models import Booking, Event
from events.notifications import send_booking_confirmation
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


def _own_booking(request, event, pk):
    """A booking reached from this session's own email, or none at all.

    Reading by contact address rather than by session-owned membership: a
    booking from the public form has no member to check against yet.
    """
    email = request.session.get(CONTACT_SESSION_KEY)
    if not email:
        return None
    return event.bookings.active().for_contact(email).filter(pk=pk).first()


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
            # Only the first booking is worth a mail: it is what carries the
            # link back here. Every later change is already confirmed on screen.
            first_time = (
                not event.bookings.active().filter(member__in=household).exists()
            )
            for member in chosen:
                Booking.objects.book(event, member)
            for booking in (
                event.bookings.active()
                .exclude(member__in=chosen)
                .filter(member__in=household)
            ):
                booking.cancel()
            if first_time:
                send_booking_confirmation(event, request.session[CONTACT_SESSION_KEY])
            return redirect("events:booked", slug=event.slug)

    return render(
        request,
        "events/book.html",
        {
            "event": event,
            "association": event.association,
            "members": household,
            "booked": set(event.bookings.active().values_list("member_id", flat=True)),
            "nobody_chosen": request.method == "POST",
        },
    )


@login_not_required
def booked(request, slug):
    event = _open_event(slug)
    email = request.session.get(CONTACT_SESSION_KEY)
    bookings = (
        event.bookings.active().for_contact(email) if email else Booking.objects.none()
    )
    return render(
        request,
        "events/booked.html",
        {
            "event": event,
            "association": event.association,
            "bookings": bookings,
            "booking_forms": [
                (booking, BookingContactForm(instance=booking)) for booking in bookings
            ],
        },
    )


@login_not_required
@require_POST
def cancel(request, slug, pk):
    """Give one person's place back — a booking is one person, not a household."""
    event = _open_event(slug)
    booking = _own_booking(request, event, pk)
    if booking is None:
        return redirect("events:landing", slug=event.slug)
    if not event.is_open:
        raise Http404("bookings are closed")

    booking.cancel()
    return redirect("events:booked", slug=event.slug)


@login_not_required
@require_POST
def edit(request, slug, pk):
    """Update the contacts and note on one booking. Names and consents belong
    to the signed application and are not rewritten from a public link."""
    event = _open_event(slug)
    booking = _own_booking(request, event, pk)
    if booking is None:
        return redirect("events:landing", slug=event.slug)
    if not event.is_open:
        raise Http404("bookings are closed")

    form = BookingContactForm(data=request.POST, instance=booking)
    if form.is_valid():
        form.save()
        request.session[CONTACT_SESSION_KEY] = form.cleaned_data["contact_email"]
    return redirect("events:booked", slug=event.slug)


@login_not_required
def manage(request, slug, token):
    """Straight back into the booking from the link in the confirmation mail.

    The token proves the address, so the tax code is not asked for a second
    time: whoever holds the mail already passed that check once.
    """
    event = _open_event(slug)
    email = email_from_token(event, token)
    if email is None:
        raise Http404("this link was not written for this event")

    if not event.is_open:
        return render(
            request,
            "events/landing.html",
            {
                "event": event,
                "association": event.association,
                "form": IdentifyForm(association=event.association),
                "link_expired": True,
            },
        )

    if not event.bookings.active().for_contact(email).exists():
        return redirect("events:landing", slug=event.slug)

    request.session[CONTACT_SESSION_KEY] = email
    return redirect("events:booked", slug=event.slug)


@login_not_required
@require_POST
def join(request, slug):
    """Not on the register yet: joining is how you book, by the current statute."""
    event = _open_event(slug)
    # An organiser can say which form an event books through; unset falls back
    # to the association's newest open one. Meta.ordering makes that first().
    public_form = event.form
    if public_form is None or not public_form.is_open:
        public_form = PublicForm.objects.filter(
            association=event.association, is_open=True
        ).first()
    if public_form is None:
        raise Http404("this association has no open application form")
    submission = Submission.objects.create(form=public_form, event=event)
    request.session["intake_draft"] = str(submission.token)
    return redirect("intake:step", token=submission.token, step=SectionKey.SUBJECT)
