import os
import tempfile
from http import HTTPStatus
from typing import Any

from core.models import Recipe, Tag
from core.models import User as CustomUser
from core.tests.factories import IngredientFactory, RecipeFactory, TagFactory, UserFactory
from django.test import TestCase
from django.urls import reverse
from faker import Faker
from PIL import Image
from rest_framework.test import APIClient, APITestCase

from recipe.serializers import RecipeDetailSerializer, RecipeSerializer


class PublicRecipeAPITests(TestCase):
    api_client: APIClient
    recipes_url: str

    @classmethod
    def setUpTestData(cls: type[PublicRecipeAPITests]) -> None:
        cls.api_client = APIClient()
        cls.recipes_url = reverse("recipe:recipe-list")

    def test_auth_required(self) -> None:
        res = self.api_client.get(self.recipes_url)

        self.assertEqual(res.status_code, HTTPStatus.UNAUTHORIZED)


class PrivateRecipeAPITests(TestCase):
    api_client: APIClient
    recipes_url: str
    user: CustomUser
    fake: Faker

    @classmethod
    def setUpTestData(cls: type[PrivateRecipeAPITests]) -> None:
        cls.api_client = APIClient()
        cls.user = UserFactory.create()
        cls.api_client.force_authenticate(cls.user)
        cls.recipes_url = reverse("recipe:recipe-list")
        cls.fake = Faker()

    def _recipe_detail_url(self, recipe_id: int) -> str:
        return reverse("recipe:recipe-detail", args=[recipe_id])

    def test_retrieve_recipes(self) -> None:
        RecipeFactory.create_batch(2, user=self.user)

        res = self.api_client.get(self.recipes_url)

        recipes = Recipe.objects.all().order_by("-id")
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_list_limited_to_user(self) -> None:
        other_user = UserFactory.create()
        RecipeFactory.create(user=self.user)
        RecipeFactory.create(user=other_user)

        res = self.api_client.get(self.recipes_url)

        recipes = Recipe.objects.all().filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_recipe_detail(self) -> None:
        recipe = RecipeFactory.create(user=self.user)
        url = self._recipe_detail_url(recipe.id)

        res = self.api_client.get(url)

        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.data, serializer.data)

    def test_create_recipe(self) -> None:
        payload = RecipeFactory.build_dict(user=self.user)

        res = self.api_client.post(self.recipes_url, payload)

        self.assertEqual(res.status_code, HTTPStatus.CREATED)
        recipe = Recipe.objects.get(id=res.data["id"])
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_partial_update(self) -> None:
        recipe = RecipeFactory.create(user=self.user)
        payload = {"title": "New recipe title"}
        url = self._recipe_detail_url(recipe.id)

        res = self.api_client.patch(url, payload)

        self.assertEqual(res.status_code, HTTPStatus.OK)
        expected = RecipeSerializer(recipe).data | payload
        recipe.refresh_from_db()
        actual = RecipeSerializer(recipe).data
        self.assertEqual(actual, expected)

    def test_full_update(self) -> None:
        recipe = RecipeFactory.create(user=self.user)
        payload = RecipeFactory.build_dict(user=self.user)
        url = self._recipe_detail_url(recipe.id)

        res = self.api_client.put(url, payload)

        self.assertEqual(res.status_code, HTTPStatus.OK)
        recipe.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    # RecipeSerializer doesn't expose the user field,
    # if someone sends {"user": 123} in the request, it's ignored.
    def test_update_user_returns_error(self) -> None:
        recipe = RecipeFactory.create(user=self.user)
        user = UserFactory.create()
        payload = {"user": user.id}
        url = self._recipe_detail_url(recipe.id)

        res = self.api_client.patch(url, payload)

        self.assertEqual(res.status_code, HTTPStatus.OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self) -> None:
        recipe = RecipeFactory.create(user=self.user)
        url = self._recipe_detail_url(recipe.id)

        res = self.api_client.delete(url)

        self.assertEqual(res.status_code, HTTPStatus.NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_recipe_other_users_recipe_error(self) -> None:
        user = UserFactory.create()
        recipe = RecipeFactory.create(user=user)
        url = self._recipe_detail_url(recipe.id)

        # RecipeViewSet.get_queryset() filters by authenticated user, so, a
        # recipe created by a different user is not present in the result.
        res = self.api_client.delete(url)

        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())

    def test_create_recipe_with_new_tags(self) -> None:
        tags = [{"name": self.fake.word()}, {"name": self.fake.word()}]
        payload = RecipeFactory.build_dict() | {"tags": tags}
        payload.pop("user")

        res = self.api_client.post(self.recipes_url, payload, format="json")

        self.assertEqual(res.status_code, HTTPStatus.CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        for tag in tags:
            exists = recipe.tags.filter(
                name=tag["name"],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_tags(self) -> None:
        tag = TagFactory.create(user=self.user)
        tags = [{"name": tag.name}, {"name": self.fake.word()}]
        payload = RecipeFactory.build_dict() | {"tags": tags}
        payload.pop("user")

        res = self.api_client.post(self.recipes_url, payload, format="json")

        self.assertEqual(res.status_code, HTTPStatus.CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(tag, recipe.tags.all())
        for t in tags:
            exists = recipe.tags.filter(
                name=t["name"],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_tag_on_update(self) -> None:
        recipe = RecipeFactory.create(user=self.user)
        tags = [{"name": self.fake.word()}]
        payload = {"tags": tags}
        url = self._recipe_detail_url(recipe.id)

        res = self.api_client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, HTTPStatus.OK)
        tag = Tag.objects.get(user=self.user, name=tags[0]["name"])
        # tags are fetched from the DB, not cached in the in-memory recipe,
        # so, no need to refresh recipe from DB.
        self.assertIn(tag, recipe.tags.all())

    def test_update_recipe_assign_tag(self) -> None:
        tag1 = TagFactory.create(user=self.user)
        recipe = RecipeFactory.create(user=self.user)
        recipe.tags.add(tag1)
        tag2 = TagFactory.create(user=self.user)
        tags = [{"name": tag2.name}]
        payload = {"tags": tags}
        url = self._recipe_detail_url(recipe.id)

        res = self.api_client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertNotIn(tag1, recipe.tags.all())
        self.assertIn(tag2, recipe.tags.all())

    def test_clear_recipe_tags(self) -> None:
        tag = TagFactory.create(user=self.user)
        recipe = RecipeFactory.create(user=self.user)
        recipe.tags.add(tag)
        payload: dict[str, list[dict[str, Any]]] = {"tags": []}
        url = self._recipe_detail_url(recipe.id)

        res = self.api_client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertEqual(recipe.tags.count(), 0)

    def test_create_recipe_with_new_ingredients(self) -> None:
        ingredients = [{"name": self.fake.word()}, {"name": self.fake.word()}]
        payload = RecipeFactory.build_dict() | {"ingredients": ingredients}
        payload.pop("user")

        res = self.api_client.post(self.recipes_url, payload, format="json")

        self.assertEqual(res.status_code, HTTPStatus.CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        for ingredient in ingredients:
            exists = recipe.ingredients.filter(
                name=ingredient["name"],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_ingredients(self) -> None:
        ingredient = IngredientFactory.create(user=self.user)
        ingredients = [{"name": ingredient.name}, {"name": self.fake.word()}]
        payload = RecipeFactory.build_dict() | {"ingredients": ingredients}
        payload.pop("user")

        res = self.api_client.post(self.recipes_url, payload, format="json")

        self.assertEqual(res.status_code, HTTPStatus.CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        self.assertIn(ingredient, recipe.ingredients.all())
        for i in ingredients:
            exists = recipe.ingredients.filter(
                name=i["name"],
                user=self.user,
            ).exists()
            self.assertTrue(exists)


class ImageUploadTests(APITestCase):
    api_client: APIClient
    user: CustomUser

    @classmethod
    def setUpTestData(cls: type[ImageUploadTests]) -> None:
        cls.api_client = APIClient()
        cls.user = UserFactory.create()
        cls.api_client.force_authenticate(cls.user)

    def setUp(self) -> None:
        self.recipe = RecipeFactory.create(user=self.user)

    def tearDown(self) -> None:
        self.recipe.image.delete()

    def _image_upload_url(self, recipe_id: int) -> str:
        return reverse("recipe:recipe-upload-image", args=[recipe_id])

    def test_upload_image(self) -> None:
        url = self._image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as image_file:
            img = Image.new("RGB", size=(10, 10))
            img.save(image_file, format="JPEG")
            # .save set EOF
            image_file.seek(0)
            payload = {"image": image_file}
            res = self.api_client.post(url, payload, format="multipart")

        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.recipe.refresh_from_db()
        self.assertIn("image", res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self) -> None:
        url = self._image_upload_url(self.recipe.id)
        payload = {"image": "notanimage"}
        res = self.api_client.post(url, payload, format="multipart")

        self.assertEqual(res.status_code, HTTPStatus.BAD_REQUEST)
