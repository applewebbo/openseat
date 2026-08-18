from datetime import timedelta

import pytest
import time_machine
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.utils import timezone

from ops.maintenance import (
    delete_orphan_media,
    orphan_media,
    purge_old_backups,
    referenced_media_names,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def media(settings, tmp_path):
    """A media root of our own, so a stray test never deletes real uploads."""
    settings.MEDIA_ROOT = tmp_path / "media"
    settings.MEDIA_ROOT.mkdir()
    return settings.MEDIA_ROOT


@pytest.fixture
def backups(settings, tmp_path):
    settings.STORAGES = {
        **settings.STORAGES,
        "dbbackup": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
            "OPTIONS": {"location": str(tmp_path / "backups")},
        },
    }
    (tmp_path / "backups").mkdir()
    return tmp_path / "backups"


def _write(root, name, when=None):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"x")
    if when is not None:
        stamp = when.timestamp()
        import os

        os.utime(path, (stamp, stamp))
    return path


# --- what the database still points at -------------------------------------


def test_a_logo_in_use_counts_as_referenced(media, association):
    association.logo.save("in-use.png", ContentFile(b"x"), save=True)

    assert association.logo.name in referenced_media_names()


def test_an_empty_file_field_references_nothing(media, association):
    assert referenced_media_names() == set()


# --- orphans ---------------------------------------------------------------


def test_a_file_nobody_references_is_an_orphan(media, association):
    old = timezone.now() - timedelta(days=2)
    _write(media, "associations/left-behind.png", when=old)

    assert "associations/left-behind.png" in orphan_media()


def test_a_file_still_in_use_is_never_an_orphan(media, association):
    association.logo.save("still-here.png", ContentFile(b"x"), save=True)
    old = timezone.now() - timedelta(days=2)
    import os

    path = media / association.logo.name
    os.utime(path, (old.timestamp(), old.timestamp()))

    assert orphan_media() == []


def test_a_freshly_uploaded_file_is_spared(media, association):
    """An upload mid-request must not be swept before its row is saved."""
    _write(media, "associations/just-now.png")

    assert orphan_media() == []


def test_deleting_orphans_removes_them_from_disk(media, association):
    old = timezone.now() - timedelta(days=2)
    path = _write(media, "associations/gone.png", when=old)

    deleted = delete_orphan_media()

    assert deleted == ["associations/gone.png"]
    assert not path.exists()


def test_a_dry_run_reports_without_deleting(media, association):
    old = timezone.now() - timedelta(days=2)
    path = _write(media, "associations/kept.png", when=old)

    deleted = delete_orphan_media(dry_run=True)

    assert deleted == ["associations/kept.png"]
    assert path.exists()


def test_an_empty_media_root_is_not_an_error(media):
    assert delete_orphan_media() == []


# --- backups ---------------------------------------------------------------


def test_a_recent_backup_is_kept(backups):
    _write(backups, "openseat-2026-08-18-000000.dump")

    with time_machine.travel(timezone.now() + timedelta(days=1), tick=False):
        assert purge_old_backups() == []


def test_a_backup_past_the_retention_window_is_deleted(backups):
    name = "openseat-2026-08-18-000000.dump"
    _write(backups, name)

    with time_machine.travel(timezone.now() + timedelta(days=31), tick=False):
        purged = purge_old_backups()

    assert purged == [name]
    assert not (backups / name).exists()


def test_media_archives_expire_on_the_same_clock(backups):
    name = "openseat-2026-08-18-000000.tar"
    _write(backups, name)

    with time_machine.travel(timezone.now() + timedelta(days=31), tick=False):
        purged = purge_old_backups()

    assert purged == [name]


def test_a_dry_run_leaves_old_backups_alone(backups):
    name = "openseat-2026-08-18-000000.dump"
    _write(backups, name)

    with time_machine.travel(timezone.now() + timedelta(days=31), tick=False):
        purged = purge_old_backups(dry_run=True)

    assert purged == [name]
    assert (backups / name).exists()


def test_files_that_are_not_backups_are_left_where_they_are(backups):
    _write(backups, "notes.txt")

    with time_machine.travel(timezone.now() + timedelta(days=400), tick=False):
        assert purge_old_backups() == []
    assert (backups / "notes.txt").exists()


# --- the command -----------------------------------------------------------


def test_the_command_sweeps_both(media, backups, association, capsys):
    old = timezone.now() - timedelta(days=2)
    _write(media, "associations/orphan.png", when=old)
    _write(backups, "openseat-2020-01-01-000000.dump")

    call_command("ops_maintenance")

    out = capsys.readouterr().out
    assert "associations/orphan.png" in out
    assert not (media / "associations/orphan.png").exists()


def test_the_command_can_be_asked_what_it_would_do(media, association, capsys):
    old = timezone.now() - timedelta(days=2)
    path = _write(media, "associations/orphan.png", when=old)

    call_command("ops_maintenance", "--dry-run")

    assert "associations/orphan.png" in capsys.readouterr().out
    assert path.exists()


def test_the_daily_sweep_can_be_registered():
    from django_q.models import Schedule

    call_command("ops_schedule")

    schedule = Schedule.objects.get(name="ops: backup and cleanup")
    assert schedule.func == "ops.maintenance.run_daily"
    assert schedule.schedule_type == Schedule.DAILY
    assert schedule.repeats == -1


def test_registering_the_daily_sweep_twice_leaves_one_job():
    from django_q.models import Schedule

    call_command("ops_schedule")
    call_command("ops_schedule")

    assert Schedule.objects.filter(name="ops: backup and cleanup").count() == 1


def test_a_caller_can_override_the_grace_window(media, association):
    _write(media, "associations/minutes-old.png")

    assert delete_orphan_media(grace_hours=0) == ["associations/minutes-old.png"]


def test_a_caller_can_override_the_retention_window(backups):
    name = "openseat-2026-08-18-000000.dump"
    _write(backups, name)

    with time_machine.travel(timezone.now() + timedelta(days=2), tick=False):
        assert purge_old_backups(days=1) == [name]


def test_the_daily_run_backs_up_before_it_deletes_anything(media, backups, association):
    """Tidying first would purge the very files this run should have saved."""
    from ops.maintenance import run_daily

    old = timezone.now() - timedelta(days=2)
    _write(media, "associations/orphan.png", when=old)
    _write(backups, "openseat-2020-01-01-000000.dump")
    seen = {}

    def record_backup():
        seen["orphan_still_there"] = (media / "associations/orphan.png").exists()
        seen["old_backup_still_there"] = (
            backups / "openseat-2020-01-01-000000.dump"
        ).exists()

    result = run_daily(backup=record_backup)

    assert seen == {"orphan_still_there": True, "old_backup_still_there": True}
    assert result["deleted_media"] == ["associations/orphan.png"]
    assert result["purged_backups"] == ["openseat-2020-01-01-000000.dump"]


# --- the deploy check ------------------------------------------------------


def test_a_missing_media_volume_fails_the_deploy_check(settings, tmp_path):
    from ops.checks import media_root_is_writable

    settings.MEDIA_ROOT = tmp_path / "never-mounted"

    errors = media_root_is_writable(None)

    assert [e.id for e in errors] == ["ops.E001"]


def test_a_read_only_media_volume_fails_the_deploy_check(settings, tmp_path):
    import os

    from ops.checks import media_root_is_writable

    root = tmp_path / "read-only"
    root.mkdir()
    os.chmod(root, 0o500)
    settings.MEDIA_ROOT = root

    try:
        errors = media_root_is_writable(None)
    finally:
        os.chmod(root, 0o700)

    assert [e.id for e in errors] == ["ops.E002"]


def test_a_mounted_media_volume_passes(media):
    from ops.checks import media_root_is_writable

    assert media_root_is_writable(None) == []
