from django.db import migrations


def backfill_birth_date(apps, schema_editor):
    Booking = apps.get_model("events", "Booking")
    for booking in Booking.objects.filter(
        birth_date__isnull=True, member__isnull=False
    ).select_related("member"):
        if booking.member.birth_date:
            booking.birth_date = booking.member.birth_date
            booking.save(update_fields=["birth_date"])

    for booking in Booking.objects.filter(
        birth_date__isnull=True, submission__isnull=False
    ).select_related("submission"):
        submission = booking.submission
        birth_date = (
            submission.member_birth_date
            if submission.subject_type and submission.subject_type != "self"
            else submission.applicant_birth_date
        )
        if birth_date:
            booking.birth_date = birth_date
            booking.save(update_fields=["birth_date"])


class Migration(migrations.Migration):
    dependencies = [
        ("events", "0007_booking_birth_date"),
    ]

    operations = [
        migrations.RunPython(backfill_birth_date, migrations.RunPython.noop),
    ]
