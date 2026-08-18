import os

from django.conf import settings
from django.core.checks import Error, register


@register(deploy=True)
def media_root_is_writable(app_configs, **kwargs):
    """Refuse a deploy whose uploads would vanish on the next redeploy.

    In production MEDIA_ROOT is expected to be a mounted volume: WhiteNoise
    serves it, but nothing makes it survive rebuilding the image. An unwritable
    or missing directory here means every association logo is lost the first
    time Coolify redeploys.
    """
    root = str(settings.MEDIA_ROOT)
    if not os.path.isdir(root):
        return [
            Error(
                f"MEDIA_ROOT does not exist: {root}",
                hint="Mount a persistent volume there, or uploads are lost on "
                "the next redeploy.",
                id="ops.E001",
            )
        ]
    if not os.access(root, os.W_OK):
        return [
            Error(
                f"MEDIA_ROOT is not writable: {root}",
                hint="The application user needs write access to the volume.",
                id="ops.E002",
            )
        ]
    return []
