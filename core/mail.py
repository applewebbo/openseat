"""A From header a spam filter reads as a real sender, not a noreply blast.

A bare noreply@ address with no display name is one of the signals spam
filters weigh most heavily. Naming the association costs nothing and, paired
with a real Reply-To, gives every outbound mail the shape of something a
person sent.
"""

import mimetypes
from email.message import MIMEPart
from email.policy import default as default_policy

from django.conf import settings

LOGO_CONTENT_ID = "association-logo"


def from_header(association):
    return f"{association.name} <{settings.DEFAULT_FROM_EMAIL}>"


def attach_logo(message, association):
    """Attach the association's logo inline, for an HTML mail's `cid:` <img>.

    Inline rather than a remote <img src>, so the logo still shows with
    remote images blocked and never depends on MEDIA_ROOT being reachable
    from the recipient's mail client. A no-op when there is no logo, so
    templates gate the <img> itself on `{% if association.logo %}`.
    """
    if association is None or not association.logo:
        return
    try:
        with association.logo.open("rb") as logo_file:
            data = logo_file.read()
    except OSError:
        return
    content_type, _ = mimetypes.guess_type(association.logo.name)
    subtype = content_type.split("/", 1)[1] if content_type else "png"
    image = MIMEPart(policy=default_policy)
    image.set_content(data, maintype="image", subtype=subtype)
    image.add_header("Content-ID", f"<{LOGO_CONTENT_ID}>")
    image.add_header("Content-Disposition", "inline", filename="logo")
    message.attach(image)
