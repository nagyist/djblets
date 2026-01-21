from __future__ import annotations

from django.urls import path


def test_url(request):
    pass


urlpatterns = [
    path('', test_url),
]
