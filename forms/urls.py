# forms/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from forms.views import FormViewSet, CategoryViewSet

app_name = 'forms'

router = DefaultRouter()
router.register(r'forms', FormViewSet, basename='form')
router.register(r'categories', CategoryViewSet, basename='category')

urlpatterns = [
    path('', include(router.urls)),
]