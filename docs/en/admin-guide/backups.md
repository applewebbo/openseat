# Backups

OpenSeat runs an automatic backup once a day, with no action needed from
the association's admin.

## What Gets Saved

Every day a database dump is created, along with a copy of the uploaded
files (logo, event images, the statute PDF). Both are kept for a number of
days set by the installation — backups older than that threshold are
deleted automatically, along with uploaded files no longer referenced by
any record in the database.

## Where They Are Kept

Depending on how the installation was configured, backups can live on local
disk or on S3-compatible storage. This configuration is technical and is
decided by whoever manages the installation, not by the association's
admin.

!!! info "Restoring a backup"
    Restoring is a technical operation, meant for whoever administers the
    installation (not for the association's day-to-day use) and requires
    direct access to the server. It is not covered in this guide.
