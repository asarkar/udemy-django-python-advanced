import random

from django.contrib.auth import get_user_model
from django.test import TestCase
from faker import Faker

from ..models import Recipe, Tag
from ..models import User as CustomUser
from .factories import RecipeFactory, UserFactory

User: type[CustomUser] = get_user_model()
fake = Faker()


def _random_case_email() -> str:
    email = fake.email()
    return "".join(char.upper() if random.choice([True, False]) else char.lower() for char in email)


class ModelTests(TestCase):
    def test_create_user_with_email_successful(self) -> None:
        email = fake.email()
        password = fake.password()
        user = User.objects.create_user(email=email, password=password)
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_domain_normalized(self) -> None:
        sample_emails = [_random_case_email() for _ in range(5)]
        for email in sample_emails:
            user = User.objects.create_user(email=email, password=fake.password())
            expected_prefix, expected_domain = email.split("@")
            actual_prefix, actual_domain = user.email.split("@")

            self.assertEqual(actual_prefix, expected_prefix)
            self.assertEqual(actual_domain, expected_domain.lower())

    def test_new_user_without_email_raises_error(self) -> None:
        with self.assertRaises(ValueError):
            User.objects.create_user(email="", password=fake.password())

    def test_create_superuser(self) -> None:
        user = User.objects.create_superuser(email=fake.email(), password=fake.password())

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_recipe(self) -> None:
        user = UserFactory.create()
        recipe = Recipe.objects.create(**RecipeFactory.build_dict(user=user))

        self.assertEqual(str(recipe), recipe.title)

    def test_create_tag(self) -> None:
        user = UserFactory.create()
        tag = Tag.objects.create(user=user, name=fake.name())

        self.assertEqual(str(tag), tag.name)
