from django.shortcuts import render


def hub(request):
    """The landing page behind the "Account" link: pick email or password."""
    return render(request, "account/hub.html")
