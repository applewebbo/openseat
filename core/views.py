from django.contrib.auth.decorators import login_not_required
from django.shortcuts import render


@login_not_required
def home(request):
    """Public landing page."""
    return render(request, "home.html")
