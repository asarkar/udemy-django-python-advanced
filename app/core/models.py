from __future__ import annotations

from typing import Any

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.db.models import ManyToManyField

from app import settings


# Why there's no circular dependency although the two classes refer to each other?
# 1. Class definitions are executed top-to-bottom - `UserManager` is fully defined before `User`
#    starts being defined.
# 2. The type hint `-> User` is just metadata - it's not executed during class definition, only
#    evaluated later for type checking.
# 3. `self.model` is set dynamically at runtime - Django assigns it when you do
#    `objects = UserManager()`, not during class definition.
class UserManager(BaseUserManager["User"]):
    def create_user(self, email: str, password: str | None = None, **kwargs: Any) -> User:
        if not email:
            raise ValueError("User must have an email address.")
        user = self.model(email=self.normalize_email(email), **kwargs)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email: str, password: str | None = None, **kwargs: Any) -> User:
        kwargs.setdefault("is_staff", True)
        kwargs.setdefault("is_superuser", True)

        return self.create_user(email, password, **kwargs)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"


class Recipe(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    time_minutes = models.IntegerField()
    price = models.DecimalField(max_digits=5, decimal_places=2)
    link = models.CharField(max_length=255, blank=True)
    tags: ManyToManyField[Tag, Any] = models.ManyToManyField("Tag")

    def __str__(self) -> str:
        return self.title


class Tag(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

    def __str__(self) -> str:
        return self.name
