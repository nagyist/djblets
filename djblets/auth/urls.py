from __future__ import unicode_literals

from django.urls import path

from djblets.auth.views import register


urlpatterns = [
    path('register/', register, kwargs={'next_page': 'test'},
         name='register'),
]
