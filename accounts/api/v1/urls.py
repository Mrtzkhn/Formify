from django.urls import path
from .views import RegisterView, LoginView, LogoutView, MeView, VersionPingView, TokenRefreshView

app_name = 'accounts_api_v1'

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('me/', MeView.as_view(), name='me'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('ping/', VersionPingView.as_view(), name='ping'),
]
