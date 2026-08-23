from allauth.account.forms import AddEmailForm as BaseAddEmailForm
from allauth.account.forms import ChangePasswordForm as BaseChangePasswordForm
from allauth.account.forms import LoginForm as BaseLoginForm
from allauth.account.forms import ResetPasswordForm as BaseResetPasswordForm
from allauth.account.forms import ResetPasswordKeyForm as BaseResetPasswordKeyForm
from allauth.account.forms import SetPasswordForm as BaseSetPasswordForm
from allauth.account.forms import SignupForm as BaseSignupForm

from core.forms import DaisyWidgetsMixin


class LoginForm(DaisyWidgetsMixin, BaseLoginForm):
    pass


class SignupForm(DaisyWidgetsMixin, BaseSignupForm):
    pass


class AddEmailForm(DaisyWidgetsMixin, BaseAddEmailForm):
    pass


class ChangePasswordForm(DaisyWidgetsMixin, BaseChangePasswordForm):
    pass


class SetPasswordForm(DaisyWidgetsMixin, BaseSetPasswordForm):
    pass


class ResetPasswordForm(DaisyWidgetsMixin, BaseResetPasswordForm):
    pass


class ResetPasswordKeyForm(DaisyWidgetsMixin, BaseResetPasswordKeyForm):
    pass
