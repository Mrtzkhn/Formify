from django.contrib import admin
from django.urls import path, include
from rest_framework.response import Response
from django.http import HttpResponse
from rest_framework.views import APIView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from drf_spectacular.utils import extend_schema

@extend_schema(
    summary="API Root",
    description="Get API information and available endpoints",
    tags=["API Information"]
)
class RootView(APIView):
    permission_classes = []
    authentication_classes = []
    def get(self, request):
        return Response(
            {
            "status": "ok", 
            "apps": ["accounts", "forms"], 
            "versions": {"accounts": ["v1"], "forms": ["v1"]}
            }
        )
    

urlpatterns = [
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('admin/', admin.site.urls),
    path('api/', RootView.as_view(), name='api-root'),
    path('api/v1/accounts/', include('accounts.api.v1.urls')),
    path('api/v1/forms/', include('forms.api.v1.urls')),
]
