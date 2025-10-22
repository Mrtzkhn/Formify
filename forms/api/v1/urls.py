# forms/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from forms.views import FormViewSet, CategoryViewSet
from forms.views.v1.views import FieldViewSet

app_name = 'forms'

router = DefaultRouter()
router.register(r'forms', FormViewSet, basename='form')
router.register(r'categories', CategoryViewSet, basename='category')

# Create v1 router with namespace
v1_router = DefaultRouter()
v1_router.register(r'fields', FieldViewSet, basename='field')

urlpatterns = [
    path('', include(router.urls)),
    path('v1/', include(v1_router.urls)),
]