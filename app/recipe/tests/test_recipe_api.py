from http import HTTPStatus

from core.models import Recipe
from core.models import User as CustomUser
from core.tests.factories import RecipeFactory, UserFactory
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from recipe.serializers import RecipeDetailSerializer, RecipeSerializer


def recipe_detail_url(recipe_id: int) -> str:
    return reverse("recipe:recipe-detail", args=[recipe_id])


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

    @classmethod
    def setUpTestData(cls: type[PrivateRecipeAPITests]) -> None:
        cls.api_client = APIClient()
        cls.user = UserFactory.create()
        cls.api_client.force_authenticate(cls.user)
        cls.recipes_url = reverse("recipe:recipe-list")

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
        url = recipe_detail_url(recipe.id)

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
        url = recipe_detail_url(recipe.id)

        res = self.api_client.patch(url, payload)

        self.assertEqual(res.status_code, HTTPStatus.OK)
        expected = RecipeSerializer(recipe).data | payload
        recipe.refresh_from_db()
        actual = RecipeSerializer(recipe).data
        self.assertEqual(actual, expected)

    def test_full_update(self) -> None:
        recipe = RecipeFactory.create(user=self.user)
        payload = RecipeFactory.build_dict(user=self.user)
        url = recipe_detail_url(recipe.id)

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
        url = recipe_detail_url(recipe.id)

        res = self.api_client.patch(url, payload)

        self.assertEqual(res.status_code, HTTPStatus.OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self) -> None:
        recipe = RecipeFactory.create(user=self.user)
        url = recipe_detail_url(recipe.id)

        res = self.api_client.delete(url)

        self.assertEqual(res.status_code, HTTPStatus.NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_recipe_other_users_recipe_error(self) -> None:
        user = UserFactory.create()
        recipe = RecipeFactory.create(user=user)
        url = recipe_detail_url(recipe.id)

        # RecipeViewSet.get_queryset() filters by authenticated user, so, a
        # recipe created by a different user is not present in the result.
        res = self.api_client.delete(url)

        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())
