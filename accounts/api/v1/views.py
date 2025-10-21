from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer, OpenApiResponse
from rest_framework_simplejwt.views import TokenRefreshView as _TokenRefreshView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status, serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.serializers import RegisterSerializer, LoginSerializer, UserSerializer, TokenPairSerializer, LogoutRequestSerializer
from accounts.services.auth import AuthService


@extend_schema_view(
    post=extend_schema(
        tags=['Accounts'],
        summary='Register',
        description='Create a new user account and return a JWT token pair.',
        request=RegisterSerializer,
        responses={
            200: TokenPairSerializer,
            400: OpenApiResponse(description='Validation error')
        }
    )
)
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            refresh, access, user = AuthService.register(**serializer.validated_data)
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'refresh': refresh, 'access': access}, status=status.HTTP_201_CREATED)


@extend_schema_view(
    post=extend_schema(
        tags=['Accounts'],
        summary='Login',
        description='Obtain a JWT token pair for an existing user',
        request=LoginSerializer,
        responses={
            200: TokenPairSerializer,
            401: OpenApiResponse(description='Invalid credentials')
        }
    )
)
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            refresh, access, user = AuthService.login(**serializer.validated_data)
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        return Response({'refresh': refresh, 'access': access})


@extend_schema_view(
    post=extend_schema(
        tags=['Accounts'],
        summary='Logout',
        description='Blacklist the provided refresh token. Returns no content on success.',
        request=LogoutRequestSerializer,
        responses={204: OpenApiResponse(description='No content')}
    )
)
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'detail': 'refresh token required'}, status=status.HTTP_400_BAD_REQUEST)
        AuthService.logout(refresh_token)
        return Response(status=status.HTTP_204_NO_CONTENT)


class TokenRefreshView(_TokenRefreshView):
    @extend_schema(
        tags=["Accounts"],
        summary="Refresh JWT",
        description="Exchange a valid refresh token for a new access token."
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
    

@extend_schema_view(
    get=extend_schema(
        tags=['Accounts'],
        summary='Me',
        description='Return the authenticated user profile.',
        responses=UserSerializer
    )
)
class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

@extend_schema_view(
    get=extend_schema(
        tags=['Accounts'],
        summary='Version ping',
        description='Simple version probe endpoint.',
        responses=inline_serializer(
            name='VersionPing',
            fields={'version': serializers.CharField()}
        )
    )
)
class VersionPingView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        return Response({'version': 'v1'})



    
