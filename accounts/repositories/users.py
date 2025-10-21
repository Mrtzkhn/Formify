from typing import Optional
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class UserRepository:
    @staticmethod
    def get_by_email(email: str) -> Optional[User]:
        return User.objects.filter(email__iexact=email).first()

    @staticmethod
    def exists_by_email(email: str) -> bool:
        return User.objects.filter(email__iexact=email).exists()

    @staticmethod
    def create_user(email: str, password: str, **extra_fields) -> User:
        return User.objects.create_user(email=email, password=password, **extra_fields)

    @staticmethod
    def update_last_login(user: User) -> None:
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
