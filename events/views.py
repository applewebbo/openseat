from django.contrib.auth.decorators import login_not_required, permission_required
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.http import require_POST
from import_export.formats.base_formats import CSV, XLSX

from events.access import email_from_contact_token, email_from_token
from events.forms import (
    BookingContactForm,
    EventCreateForm,
    IdentifyForm,
    ManualBookingForm,
    RecoverForm,
)
from events.models import Booking, Event, FeeMethod
from events.notifications import send_booking_confirmation, send_booking_links
from events.throttle import claim_send
from intake.models import (
    Association,
    PublicForm,
    SectionKey,
    SubjectType,
    Submission,
    Subscription,
)
from members.models import Member
from members.resources import MemberResource

CONTACT_SESSION_KEY = "events_contact"

EXPORT_FORMATS = {"csv": CSV(), "xlsx": XLSX()}


def _open_event(slug):
    return get_object_or_404(Event, slug=slug, is_published=True)


def _manage_url(event):
    """Back to the management view, not the public one an editor started on."""
    return f"{event.get_absolute_url()}?view=manage"


def _public_form_for(event):
    """Which form a booking through this event is signed on.

    An organiser can pin one to the event; unset falls back to the
    association's newest open one. Meta.ordering makes that first().
    """
    public_form = event.form
    if public_form is None or not public_form.is_open:
        public_form = PublicForm.objects.filter(
            association=event.association, is_open=True
        ).first()
    return public_form


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


def _booking_summary(event, bookings):
    """Counts for the editor's summary card: total, confirmed, and a per-age
    bracket breakdown of all active bookings — an unknown-age bucket catches
    bookings with no birth_date on record.

    Takes the already-fetched active bookings rather than querying its own
    copy, so a caller that also lists them pays for one query, not two."""
    active = list(bookings)
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
        {"summary": _booking_summary(event, event.bookings.active()), "oob": True},
        request=request,
    )
    return HttpResponse(row + summary)


@permission_required("events.add_event", raise_exception=True)
def create(request):
    """An editor's own way to add an event, next to the admin.

    Nothing to book into without an open membership form, so the page shows
    a plain notice instead of a form with nothing to submit.
    """
    association = Association.current()
    if not PublicForm.objects.filter(association=association, is_open=True).exists():
        return render(
            request,
            "events/create.html",
            {"association": association, "no_open_forms": True},
        )
    if request.method == "POST":
        form = EventCreateForm(request.POST, request.FILES, association=association)
        if form.is_valid():
            event = form.save()
            return redirect("events:landing", slug=event.slug)
    else:
        form = EventCreateForm(association=association)
    return render(
        request, "events/create.html", {"form": form, "association": association}
    )


@login_not_required
def landing(request, slug):
    """The event, and the two ways in: already a member, or not yet.

    Default view is the public one, for an editor same as for a visitor — a
    "Manage" button swaps client-side into the bookings/check-in view, and a
    "View" button swaps back. Both swaps target #sheet and never push a URL,
    so a shared or reloaded link always lands on the public page."""
    event = _open_event(slug)
    can_manage_checkin = request.user.is_authenticated and request.user.has_perm(
        "events.change_event"
    )
    wants_manage = can_manage_checkin and request.GET.get("view") == "manage"

    if wants_manage:
        query = request.GET.get("q", "").strip()
        active_bookings = event.bookings.active()
        context = {
            "event": event,
            "association": event.association,
            "bookings": _matching(active_bookings, query),
            "query": query,
            "can_manage_checkin": can_manage_checkin,
        }
        if request.htmx and request.htmx.target == "roster":
            template = "events/checkin-roster-partial.html"
        else:
            context["summary"] = _booking_summary(event, active_bookings)
            context["add_form"] = ManualBookingForm(event=event)
            template = (
                "events/checkin-sheet-partial.html"
                if request.htmx
                else "events/checkin.html"
            )
        return render(request, template, context)

    template = (
        "events/landing-sheet-partial.html" if request.htmx else "events/landing.html"
    )
    return render(
        request,
        template,
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
    return redirect(_manage_url(event))


@permission_required("events.change_event", raise_exception=True)
@require_POST
def checkin_close(request, slug):
    """Undoes checkin_open — a mistake at the door should not need the admin."""
    event = _open_event(slug)
    if event.checkin_started_at is not None:
        event.checkin_started_at = None
        event.save(update_fields=["checkin_started_at"])
    return redirect(_manage_url(event))


@permission_required("events.export_members", raise_exception=True)
def export_members(request, slug):
    """The register on the external tracciato, but only who joined here.

    "Acquired at this event" means a first-time member: their submission's
    only booking is this one. Someone who joined earlier and simply rebooked
    is already on the register, so they are not counted again here.
    """
    event = _open_event(slug)
    export_format = EXPORT_FORMATS.get(request.GET.get("format"))
    if export_format is None:
        raise Http404
    members = Member.objects.filter(submission__booking__event=event)
    dataset = MemberResource().export(members)
    data = export_format.export_data(dataset)
    response = HttpResponse(data, content_type=export_format.get_content_type())
    filename = f"soci-{event.slug}.{export_format.get_extension()}"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


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
    return redirect(_manage_url(event))


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
    return redirect(_manage_url(event))


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
    public_form = _public_form_for(event)
    if public_form is None:
        raise Http404("this association has no open application form")
    submission = Submission.objects.create(form=public_form, event=event)
    request.session["intake_draft"] = str(submission.token)
    return redirect("intake:step", token=submission.token, step=SectionKey.SUBJECT)


def _member_initial(member, role):
    """What a matched register entry offers to prefill a section with."""
    prefix = f"{role}_"
    initial = {
        f"{prefix}first_name": member.first_name,
        f"{prefix}last_name": member.last_name,
        f"{prefix}birth_date": member.birth_date,
        f"{prefix}birth_place": member.birth_place,
        f"{prefix}tax_code": member.tax_code,
        f"{prefix}street": member.street,
        f"{prefix}number": member.number,
        f"{prefix}city": member.city,
    }
    if role == "applicant":
        initial["applicant_phone"] = member.contact_phone
        initial["applicant_email"] = member.email or member.contact_email
    return initial


def _applicant_initial_from_contact(member):
    """A best-effort guess at the parent's own details, from who the
    register writes to — the register holds no more than that about them.

    The address is the child's own: a parent living elsewhere corrects it,
    but living together is the common case worth defaulting to.
    """
    first_name, _, last_name = member.contact_name.strip().partition(" ")
    initial = {}
    if first_name:
        initial["applicant_first_name"] = first_name
    if last_name:
        initial["applicant_last_name"] = last_name
    if member.contact_email:
        initial["applicant_email"] = member.contact_email
    if member.contact_phone:
        initial["applicant_phone"] = member.contact_phone
    if member.street:
        initial["applicant_street"] = member.street
    if member.number:
        initial["applicant_number"] = member.number
    if member.city:
        initial["applicant_city"] = member.city
    return initial


def _mark_prefilled(form, field_names):
    """Flag fields filled from the register with a visible green border."""
    for name in field_names:
        field = form.fields.get(name)
        if field:
            field.widget.attrs["class"] += " border-success! bg-success/5"


def _age_today(birth_date):
    today = timezone.localdate()
    years = today.year - birth_date.year
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        years -= 1
    return years


def _resolved_subject_type(member):
    """Whether an already-registered member books as themselves or as a minor.

    Their own application, if any, said so exactly. Absent that — an entry
    made by hand from a paper form — a birth date under 18 is the next best
    signal; with neither, assume an adult booking for themselves.
    """
    if member.submission_id and member.submission.subject_type:
        return member.submission.subject_type
    if member.birth_date and _age_today(member.birth_date) < 18:
        return SubjectType.MINOR
    return SubjectType.SELF


@permission_required("events.add_booking", raise_exception=True)
def checkin_lookup(request, slug):
    """The "already a member" search: a tax code checked against the register."""
    event = _open_event(slug)
    tax_code = request.GET.get("existing_tax_code", "").strip()
    match = None
    if tax_code:
        match = Member.objects.filter(
            association=event.association, tax_code__iexact=tax_code
        ).first()
    if match is None:
        return render(
            request,
            "events/checkin-add-existing-search-partial.html",
            {
                "event": event,
                "found": False,
                "tax_code": tax_code,
                "not_found": bool(tax_code),
            },
        )

    resolved_type = _resolved_subject_type(match)
    applies_for_someone_else = resolved_type != SubjectType.SELF

    html = render_to_string(
        "events/checkin-add-existing-search-partial.html",
        {
            "event": event,
            "found": True,
            "resolved_type": resolved_type,
            "full_name": match.full_name,
        },
        request=request,
    )

    applicant_initial = (
        _applicant_initial_from_contact(match)
        if applies_for_someone_else
        else _member_initial(match, "applicant")
    )
    applicant_form = ManualBookingForm(initial=applicant_initial, event=event)
    _mark_prefilled(applicant_form, applicant_initial.keys())
    html += render_to_string(
        "events/checkin-add-applicant-fields-partial.html",
        {"form": applicant_form, "event": event, "oob": True},
        request=request,
    )

    if applies_for_someone_else:
        member_initial = _member_initial(match, "member")
        member_form = ManualBookingForm(initial=member_initial, event=event)
        _mark_prefilled(member_form, member_initial.keys())
        html += render_to_string(
            "events/checkin-add-member-fields-partial.html",
            {"form": member_form, "event": event, "oob": True},
            request=request,
        )

    return HttpResponse(html)


def _checkin_add_context(event, add_form):
    active_bookings = event.bookings.active()
    return {
        "event": event,
        "association": event.association,
        "bookings": active_bookings,
        "query": "",
        "can_manage_checkin": True,
        "summary": _booking_summary(event, active_bookings),
        "add_form": add_form,
    }


@permission_required("events.add_booking", raise_exception=True)
@require_POST
def checkin_add(request, slug):
    """A booking taken from a paper form signed at the door — already confirmed."""
    event = _open_event(slug)
    form = ManualBookingForm(data=request.POST, event=event)
    if not form.is_valid():
        return render(request, "events/checkin.html", _checkin_add_context(event, form))

    public_form = _public_form_for(event)
    if public_form is None:
        raise Http404("this association has no open application form")

    data = form.cleaned_data
    subject_type = data["subject_type"]
    applies_for_someone_else = subject_type != SubjectType.SELF

    submission = Submission(
        form=public_form,
        event=event,
        subject_type=subject_type,
        state=Submission.State.SUBMITTED,
        submitted_at=timezone.now(),
        accepts_statute=True,
        sole_holder=data["sole_holder"] if applies_for_someone_else else None,
        consent_images=data["consent_images"],
        consent_whatsapp=data["consent_whatsapp"],
        applicant_first_name=data["applicant_first_name"],
        applicant_last_name=data["applicant_last_name"],
        applicant_birth_date=data["applicant_birth_date"],
        applicant_birth_place=data["applicant_birth_place"],
        applicant_tax_code=data["applicant_tax_code"],
        applicant_street=data["applicant_street"],
        applicant_number=data["applicant_number"],
        applicant_postcode=data["applicant_postcode"],
        applicant_city=data["applicant_city"],
        applicant_phone=data["applicant_phone"],
        applicant_email=data["applicant_email"],
    )
    if applies_for_someone_else:
        submission.member_first_name = data["member_first_name"]
        submission.member_last_name = data["member_last_name"]
        submission.member_birth_date = data["member_birth_date"]
        submission.member_birth_place = data["member_birth_place"]
        submission.member_tax_code = data["member_tax_code"]
        submission.member_street = data["member_street"]
        submission.member_number = data["member_number"]
        submission.member_city = data["member_city"]
        if not data["sole_holder"]:
            submission.second_parent_first_name = data["second_parent_first_name"]
            submission.second_parent_last_name = data["second_parent_last_name"]
    submission.save()

    now = timezone.now()
    Subscription.objects.create(
        submission=submission,
        signatory_name=submission.applicant_name,
        role=Subscription.Role.PRIMARY,
        subject=Subscription.Subject.MEMBERSHIP,
        state=Subscription.State.SIGNED,
        signed_at=now,
    )
    if submission.needs_second_parent and (
        data["consent_images"] or data["consent_whatsapp"]
    ):
        Subscription.objects.create(
            submission=submission,
            signatory_name=(
                f"{data['second_parent_first_name']} {data['second_parent_last_name']}"
            ).strip(),
            role=Subscription.Role.SECOND_PARENT,
            subject=Subscription.Subject.IMAGE_CONSENT,
            state=Subscription.State.SIGNED,
            signed_at=now,
        )

    booking = Booking.objects.book_application(event, submission)
    booking.confirmed_on = timezone.localdate()
    booking.fee_amount = event.association.membership_fee
    booking.fee_method = FeeMethod.CASH
    booking.save(update_fields=["confirmed_on", "fee_amount", "fee_method", "member"])

    return redirect(_manage_url(event))
