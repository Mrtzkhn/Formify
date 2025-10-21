from typing import Tuple
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.repositories.users import UserRepository

class AuthService:
    @staticmethod
    def register(email: str, password: str, full_name: str = '', phone_number: str = '') -> Tuple[str, str, object]:
        if UserRepository.exists_by_email(email):
            raise ValueError('A user with this email already exists.')
        user = UserRepository.create_user(email=email, password=password, full_name=full_name, phone_number=phone_number)
        refresh = RefreshToken.for_user(user)
        return str(refresh), str(refresh.access_token), user

    @staticmethod
    def login(email: str, password: str) -> Tuple[str, str, object]:
        user = authenticate(username=email, password=password)
        if not user:
            raise ValueError('Invalid credentials.')
        UserRepository.update_last_login(user)
        refresh = RefreshToken.for_user(user)
        return str(refresh), str(refresh.access_token), user

    @staticmethod
    def logout(refresh_token: str) -> None:
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            # ignore non-blacklist or invalid token cases
            pass
