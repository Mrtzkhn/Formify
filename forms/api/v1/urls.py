from django.urls import path, include
from rest_framework.routers import DefaultRouter
from forms.api.v1.views import FieldViewSet

app_name = 'forms_v1'

# Create router for API v1
router = DefaultRouter()
router.register(r'fields', FieldViewSet, basename='field')

urlpatterns = [
    path('', include(router.urls)),
]