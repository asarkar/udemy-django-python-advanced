import random
from decimal import Decimal
from typing import Any

import factory
from django.db import models
from factory.django import DjangoModelFactory

from ..models import Recipe, Tag, User


class BaseFactory[T: models.Model](DjangoModelFactory[T]):
    """Base factory with common utilities for all model factories."""

    class Meta:
        abstract = True

    @classmethod
    def build_dict(cls, **kwargs: Any) -> dict[str, Any]:
        """Build a dictionary of model attributes without saving to database."""
        return factory.build(dict, FACTORY_CLASS=cls, **kwargs)


class UserFactory(BaseFactory[User]):
    class Meta:
        model = User

    email = factory.Faker("email")
    name = factory.Faker("name")
    password = factory.Faker("password")
    is_active = True
    is_staff = False
    is_superuser = False

    @classmethod
    def _create(cls, model_class: type[User], *args: Any, **kwargs: Any) -> User:
        """Override the default _create to use create_user method."""
        password: str | None = kwargs.pop("password", None)
        is_superuser: bool = kwargs.get("is_superuser", False)
        manager = cls._get_manager(model_class)

        # Use create_superuser if is_superuser is True
        if is_superuser and hasattr(manager, "create_superuser"):
            email: str = kwargs["email"]
            return manager.create_superuser(email, password=password)

        # Otherwise use create_user
        if hasattr(manager, "create_user"):
            return manager.create_user(*args, password=password, **kwargs)

        return super()._create(model_class, *args, **kwargs)


class RecipeFactory(BaseFactory[Recipe]):
    class Meta:
        model = Recipe

    user = factory.SubFactory(UserFactory)
    title = factory.Faker("sentence", nb_words=4)
    description = factory.Faker("paragraph")
    time_minutes = factory.Faker("random_int", min=5, max=180)
    price = factory.LazyAttribute(
        lambda _: Decimal(f"{random.randint(5, 100)}.{random.randint(0, 99):02d}")
    )
    link = factory.Faker("url")

    # M2M fields require a saved instance before we can write to them.
    #
    # Django M2M fields are not simple attributes. Internally:
    # - `recipe.tags` is a `RelatedManager`, not a list
    # - Cannot assign like `recipe.tags = [...]`
    # - Must call `.add()` _after_ the instance is saved
    #
    # Because the M2M relation uses a separate join table, Django needs the `recipe.id` first.
    @factory.post_generation
    def tags(
        self,
        create: bool,
        extracted: list[Tag] | None,
    ) -> None:
        """
        Many-to-many field handler.
        - Default: empty list
        - If tags are provided: add them after instance is saved
        """
        if not create or not extracted:
            return

        for tag in extracted:
            if tag.pk is None:
                tag.save()
            self.tags.add(tag)


class TagFactory(BaseFactory[Tag]):
    class Meta:
        model = Tag

    user = factory.SubFactory(UserFactory)
    name = factory.Faker("word")
