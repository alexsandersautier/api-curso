from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserRole(models.TextChoices):
    CUSTOMER = "customer", "Customer"
    ADMIN = "admin", "Admin"


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email: str, password: str | None = None, **extra_fields):
        normalized_email = self.normalize_email(email.strip().lower()) if email else ""
        if not normalized_email:
            raise ValueError("The email address is required.")

        user = self.model(email=normalized_email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str | None = None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=8,
        choices=UserRole.choices,
        default=UserRole.CUSTOMER,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    objects = UserManager()

    def __str__(self) -> str:
        return self.email
