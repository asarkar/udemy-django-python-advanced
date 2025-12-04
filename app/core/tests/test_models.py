import random
from pathlib import PurePosixPath
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from faker import Faker

from core import models
from core.models import Ingredient, Recipe, Tag
from core.models import User as CustomUser
from core.tests.factories import RecipeFactory, UserFactory

User: type[CustomUser] = get_user_model()


class ModelTests(TestCase):
    fake: Faker

    @classmethod
    def setUpTestData(cls: type[ModelTests]) -> None:
        cls.fake = Faker()

    def test_create_user_with_email_successful(self) -> None:
        email = self.fake.email()
        password = self.fake.password()
        user = User.objects.create_user(email=email, password=password)
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def _random_case_email(self) -> str:
        email = self.fake.email()
        return "".join(
            char.upper() if random.choice([True, False]) else char.lower() for char in email
        )

    def test_new_user_email_domain_normalized(self) -> None:
        sample_emails = [self._random_case_email() for _ in range(5)]
        for email in sample_emails:
            user = User.objects.create_user(email=email, password=self.fake.password())
            expected_prefix, expected_domain = email.split("@")
            actual_prefix, actual_domain = user.email.split("@")

            self.assertEqual(actual_prefix, expected_prefix)
            self.assertEqual(actual_domain, expected_domain.lower())

    def test_new_user_without_email_raises_error(self) -> None:
        with self.assertRaises(ValueError):
            User.objects.create_user(email="", password=self.fake.password())

    def test_create_superuser(self) -> None:
        user = User.objects.create_superuser(email=self.fake.email(), password=self.fake.password())

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_recipe(self) -> None:
        user = UserFactory.create()
        recipe = Recipe.objects.create(**RecipeFactory.build_dict(user=user))

        self.assertEqual(str(recipe), recipe.title)

    def test_create_tag(self) -> None:
        user = UserFactory.create()
        tag = Tag.objects.create(user=user, name=self.fake.name())

        self.assertEqual(str(tag), tag.name)

    def test_create_ingredient(self) -> None:
        user = UserFactory.create()
        ingredient = Ingredient.objects.create(user=user, name=self.fake.name())
        self.assertEqual(str(ingredient), ingredient.name)

    @patch("core.models.uuid.uuid4")
    def test_recipe_file_name_uuid(self, mock_uuid: MagicMock) -> None:
        mock_uuid.return_value = "test-uuid"

        file_path = models.recipe_image_file_path(None, "image.jpg")

        expected = "recipe/test-uuid.jpg"
        # PurePosixPath(...).as_posix() gives a consistent "recipe/test-uuid.jpg" string
        # regardless of what the OS separator is (\ vs /).
        self.assertEqual(PurePosixPath(file_path).as_posix(), expected)
