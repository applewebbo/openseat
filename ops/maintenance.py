"""Housekeeping the host would otherwise accumulate: old backups, stray files."""

import logging
from datetime import timedelta

from dbbackup import utils
from django.apps import apps
from django.conf import settings
from django.core.files.storage import default_storage, storages
from django.core.management import call_command
from django.db import models
from django.utils import timezone

logger = logging.getLogger(__name__)


def referenced_media_names():
    """Every file path the database still points at, across every model."""
    names = set()
    for model in apps.get_models():
        fields = [
            field.name
            for field in model._meta.get_fields()
            if isinstance(field, models.FileField)
        ]
        if not fields:
            continue
        for field in fields:
            names.update(
                model._default_manager.exclude(**{field: ""})
                .exclude(**{f"{field}__isnull": True})
                .values_list(field, flat=True)
            )
    return names


def _listdir(storage, path=""):
    """Contents of a storage path, treating "not there yet" as empty.

    Neither MEDIA_ROOT nor the backup destination exists on a fresh install
    until something is written, and a sweep that runs first must not crash.
    """
    try:
        return storage.listdir(path)
    except FileNotFoundError:
        return [], []


def _walk(path=""):
    """Every file under the media storage, as storage-relative names."""
    directories, files = _listdir(default_storage, path)
    for name in files:
        yield f"{path}/{name}" if path else name
    for directory in directories:
        yield from _walk(f"{path}/{directory}" if path else directory)


def orphan_media(grace_hours=None):
    """Files on disk that nothing references any more.

    Anything written in the last few hours is spared: an upload is on disk
    before its row is saved, and a sweep in between would delete a file
    somebody is still in the middle of attaching.
    """
    if grace_hours is None:
        grace_hours = settings.MEDIA_ORPHAN_GRACE_HOURS
    cutoff = timezone.now() - timedelta(hours=grace_hours)
    referenced = referenced_media_names()
    orphans = []
    for name in _walk():
        if name in referenced:
            continue
        if default_storage.get_modified_time(name) >= _naive_if_needed(cutoff):
            continue
        orphans.append(name)
    return sorted(orphans)


def _naive_if_needed(moment):
    """FileSystemStorage reports naive times unless USE_TZ storages say otherwise."""
    return moment if settings.USE_TZ else timezone.make_naive(moment)


def delete_orphan_media(dry_run=False, grace_hours=None):
    orphans = orphan_media(grace_hours=grace_hours)
    for name in orphans:
        logger.info("orphan media %s%s", name, " (dry run)" if dry_run else "")
        if not dry_run:
            default_storage.delete(name)
    return orphans


def purge_old_backups(dry_run=False, days=None):
    """Delete backups older than the retention window.

    dbbackup's own cleanup keeps a count, not an age, so this is the piece that
    answers "nothing older than thirty days". It reads the destination from
    Django's storages registry rather than dbbackup's own helper, which copies
    the settings once at import and would ignore any later change.
    """
    if days is None:
        days = settings.BACKUP_RETENTION_DAYS
    storage = storages["dbbackup"]
    cutoff = timezone.now() - timedelta(days=days)
    purged = []
    for name in _listdir(storage)[1]:
        taken = utils.filename_to_date(name)
        # Anything whose name carries no backup timestamp was put there by
        # somebody else, so it is not ours to delete.
        if taken is None:
            continue
        if timezone.make_aware(taken) >= cutoff:
            continue
        logger.info("expired backup %s%s", name, " (dry run)" if dry_run else "")
        if not dry_run:
            storage.delete(name)
        purged.append(name)
    return sorted(purged)


def run_backup():  # pragma: no cover - two passthroughs to dbbackup's commands
    """Database and media, to whatever storage the dbbackup alias points at.

    Not exercised by the suite: dumping a real database is a deploy-time
    concern, and driving dbbackup against the in-memory test database hangs
    rather than proving anything. run_daily's own test injects a stand-in.
    """
    call_command("dbbackup", "--clean", "--noinput")
    call_command("mediabackup", "--clean", "--noinput")


def run_daily(backup=run_backup):
    """One entry point for the scheduler: back up, then tidy.

    The backup step is a parameter so the order of operations can be tested
    without a real dump: tidying before backing up would purge files that this
    run was supposed to preserve.
    """
    backup()
    return {
        "purged_backups": purge_old_backups(),
        "deleted_media": delete_orphan_media(),
    }
