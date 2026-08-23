"""A new login waits for a superuser's approval before it works.

Regular sign-ups deactivate on `email_confirmed`, once the address is known
good, rather than at signup time - deactivating earlier would pre-empt
allauth's own "check your inbox" stage. Social providers that already vouch
for the address (Google, with VERIFIED_EMAIL) skip that stage entirely, so
`user_signed_up` is where their email first shows up verified.
"""

from django.dispatch import receiver

from allauth.account.signals import email_confirmed, user_signed_up

from accounts.notifications import send_approval_request


def _await_approval(user):
    if not user.is_active:
        return
    user.is_active = False
    user.save(update_fields=["is_active"])
    send_approval_request(user)


@receiver(user_signed_up)
def deactivate_pre_verified_signup(request, user, **kwargs):
    if user.emailaddress_set.filter(verified=True).exists():
        _await_approval(user)


@receiver(email_confirmed)
def deactivate_on_email_confirmed(request, email_address, **kwargs):
    _await_approval(email_address.user)
