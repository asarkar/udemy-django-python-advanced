from typing import Any

import factory
from factory.django import DjangoModelFactory

from ..models import User


class UserFactory(DjangoModelFactory[User]):
    class Meta:
        model = User

    email = factory.Faker("email")  # type: ignore[attr-defined, no-untyped-call]
    name = factory.Faker("name")  # type: ignore[attr-defined, no-untyped-call]
    password = factory.Faker("password")  # type: ignore[attr-defined, no-untyped-call]
    is_active = True
    is_staff = False
    is_superuser = False

    @classmethod
    def build_dict(cls, **kwargs: Any) -> dict[str, Any]:
        """Build a dictionary of user attributes."""
        return factory.build(dict, FACTORY_CLASS=cls, **kwargs)  # type: ignore[attr-defined, no-untyped-call, no-any-return]

    @classmethod
    def _create(cls, model_class: type[User], *args: Any, **kwargs: Any) -> User:
        """Override the default _create to use create_user method."""
        password: str | None = kwargs.pop("password", None)
        is_superuser: bool = kwargs.get("is_superuser", False)
        manager = cls._get_manager(model_class)  # type: ignore[no-untyped-call]

        # Use create_superuser if is_superuser is True
        if is_superuser and hasattr(manager, "create_superuser"):
            email: str = kwargs["email"]
            return manager.create_superuser(email, password=password)  # type: ignore[no-any-return]

        # Otherwise use create_user
        if hasattr(manager, "create_user"):
            return manager.create_user(*args, password=password, **kwargs)  # type: ignore[no-any-return]

        return super()._create(model_class, *args, **kwargs)  # type: ignore[no-untyped-call, no-any-return]
