# forms/urls.py
from django.urls import path, include

app_name = 'forms'

urlpatterns = [
    path('api/v1/', include('forms.api.v1.urls')),
]
