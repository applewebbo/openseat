from django.conf import settings
from whitenoise.middleware import WhiteNoiseMiddleware


class MediaWhiteNoiseMiddleware(WhiteNoiseMiddleware):
    """WhiteNoise, taught to serve MEDIA_ROOT as well as STATIC_ROOT.

    Uploads are a handful of association logos on a mounted volume, which is
    simpler than a bucket and keeps the files on the association's own machine.
    Nothing else in the stack serves them: Django's static() helper is
    DEBUG-only, and this middleware sits ahead of LoginRequiredMiddleware, so a
    public form shows its logo to visitors who have no account by design.
    """

    def __init__(self, get_response=None, settings=settings):
        super().__init__(get_response, settings=settings)
        self.add_files(settings.MEDIA_ROOT, prefix=settings.MEDIA_URL)
