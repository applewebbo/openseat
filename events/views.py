from django.contrib.auth.decorators import login_not_required, permission_required
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.http import require_POST

from events.access import email_from_contact_token, email_from_token
from events.forms import BookingContactForm, IdentifyForm, RecoverForm
from events.models import Booking, Event, FeeMethod
from events.notifications import send_booking_confirmation, send_booking_links
from events.throttle import claim_send
from intake.models import Association, PublicForm, SectionKey, Submission
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


def _matching(bookings, query):
    if not query:
        return bookings
    return bookings.filter(
        Q(first_name__icontains=query)
        | Q(last_name__icontains=query)
        | Q(contact_name__icontains=query)
    )


def _booking_summary(event):
    """Counts for the editor's summary card: total, confirmed, and a per-age
    bracket breakdown of all active bookings — an unknown-age bucket catches
    bookings with no birth_date on record."""
    active = list(event.bookings.active())
    brackets = list(event.association.age_brackets.all())
    booked = dict.fromkeys((b.pk for b in brackets), 0)
    unknown_booked = 0
    confirmed_total = 0
    for booking in active:
        if booking.is_confirmed:
            confirmed_total += 1
        age = booking.age_at_booking
        matched = next(
            (b for b in brackets if age is not None and b.matches(age)), None
        )
        if matched is None:
            unknown_booked += 1
        else:
            booked[matched.pk] += 1
    return {
        "total": len(active),
        "confirmed": confirmed_total,
        "brackets": [(b, booked[b.pk]) for b in brackets],
        "unknown_booked": unknown_booked,
    }


def _row_and_summary(request, event, booking):
    """The row swap plus an out-of-band refresh of the summary card."""
    row = render_to_string(
        "events/checkin-row-partial.html",
        {"event": event, "booking": booking},
        request=request,
    )
    summary = render_to_string(
        "events/checkin-summary-partial.html",
        {"summary": _booking_summary(event), "oob": True},
        request=request,
    )
    return HttpResponse(row + summary)


@login_not_required
def landing(request, slug):
    """The event, and the two ways in: already a member, or not yet.

    An editor never sees the public page: this is always the bookings list
    for them, filtered live by the search box through htmx. Check-in actions
    on it only light up once bookings are closed."""
    event = _open_event(slug)
    can_manage_checkin = request.user.is_authenticated and request.user.has_perm(
        "events.change_event"
    )
    if can_manage_checkin:
        query = request.GET.get("q", "").strip()
        context = {
            "event": event,
            "association": event.association,
            "bookings": _matching(event.bookings.active(), query),
            "query": query,
            "can_manage_checkin": can_manage_checkin,
        }
        if request.htmx:
            template = "events/checkin-roster-partial.html"
        else:
            template = "events/checkin.html"
            context["summary"] = _booking_summary(event)
        return render(request, template, context)

    return render(
        request,
        "events/landing.html",
        {
            "event": event,
            "association": event.association,
            "form": IdentifyForm(association=event.association),
            "can_manage_checkin": can_manage_checkin,
        },
    )


@permission_required("events.change_event", raise_exception=True)
@require_POST
def checkin_open(request, slug):
    """An editor at the door: from here on the clock no longer decides."""
    event = _open_event(slug)
    if event.checkin_started_at is None:
        event.checkin_started_at = timezone.now()
        event.save(update_fields=["checkin_started_at"])
    return redirect("events:landing", slug=event.slug)


@permission_required("events.change_event", raise_exception=True)
@require_POST
def checkin_close(request, slug):
    """Undoes checkin_open — a mistake at the door should not need the admin."""
    event = _open_event(slug)
    if event.checkin_started_at is not None:
        event.checkin_started_at = None
        event.save(update_fields=["checkin_started_at"])
    return redirect("events:landing", slug=event.slug)


@permission_required("events.change_booking", raise_exception=True)
@require_POST
def checkin_confirm(request, slug, pk):
    """Checking in at the door is how a booking is confirmed — there is no
    online payment yet, so the fee is always the membership fee, in cash."""
    event = _open_event(slug)
    if event.is_open:
        raise Http404
    booking = get_object_or_404(event.bookings.active(), pk=pk)
    if booking.confirmed_on is None:
        booking.confirmed_on = timezone.localdate()
        booking.fee_amount = event.association.membership_fee
        booking.fee_method = FeeMethod.CASH
        booking.save(update_fields=["confirmed_on", "fee_amount", "fee_method"])
    if request.htmx:
        return _row_and_summary(request, event, booking)
    return redirect("events:landing", slug=event.slug)


@permission_required("events.change_booking", raise_exception=True)
@require_POST
def checkin_undo(request, slug, pk):
    """A mistake at the door — checked in the wrong person, or too soon."""
    event = _open_event(slug)
    if event.is_open:
        raise Http404
    booking = get_object_or_404(event.bookings.active(), pk=pk)
    if booking.confirmed_on is not None:
        booking.confirmed_on = None
        booking.fee_amount = None
        booking.fee_method = ""
        booking.save(update_fields=["confirmed_on", "fee_amount", "fee_method"])
    if request.htmx:
        return _row_and_summary(request, event, booking)
    return redirect("events:landing", slug=event.slug)


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
def recover(request):
    """Ask for the link back into your bookings, with only your address.

    The answer never says whether the address booked anything: a form that
    told them apart would let anybody test addresses one at a time.
    """
    association = Association.current()
    form = RecoverForm(data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"]
        if claim_send(email):
            send_booking_links(email)
        return redirect("events:recover-sent")

    return render(
        request,
        "events/recover.html",
        {"association": association, "form": form},
    )


@login_not_required
def recover_sent(request):
    """The same words either way, and how to reach a human if none arrives."""
    return render(
        request,
        "events/recover-sent.html",
        {"association": Association.current()},
    )


@login_not_required
def mine(request, token):
    """Everything one address has booked, from the link mailed to it."""
    email = email_from_contact_token(token)
    if email is None:
        return render(
            request,
            "events/recover.html",
            {
                "association": Association.current(),
                "form": RecoverForm(),
                "link_expired": True,
            },
        )

    bookings = Booking.objects.active().for_contact(email).upcoming()
    request.session[CONTACT_SESSION_KEY] = email
    return render(
        request,
        "events/mine.html",
        {
            "association": Association.current(),
            "bookings": bookings,
            "booking_forms": [
                (booking, BookingContactForm(instance=booking)) for booking in bookings
            ],
        },
    )


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
