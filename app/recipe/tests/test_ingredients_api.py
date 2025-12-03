from http import HTTPStatus

from core.models import Ingredient
from core.models import User as CustomUser
from core.tests.factories import IngredientFactory, RecipeFactory, UserFactory
from django.test import TestCase
from django.urls import reverse
from faker import Faker
from rest_framework.test import APIClient

from recipe.serializers import IngredientSerializer


class PublicIngredientsAPITests(TestCase):
    api_client: APIClient
    ingredients_url: str

    @classmethod
    def setUpTestData(cls: type[PublicIngredientsAPITests]) -> None:
        cls.api_client = APIClient()
        cls.ingredients_url = reverse("recipe:ingredient-list")

    def test_auth_required(self) -> None:
        res = self.api_client.get(self.ingredients_url)

        self.assertEqual(res.status_code, HTTPStatus.UNAUTHORIZED)


class PrivateIngredientsAPITests(TestCase):
    api_client: APIClient
    ingredients_url: str
    user: CustomUser
    fake: Faker

    @classmethod
    def setUpTestData(cls: type[PrivateIngredientsAPITests]) -> None:
        cls.api_client = APIClient()
        cls.user = UserFactory.create()
        cls.api_client.force_authenticate(cls.user)
        cls.ingredients_url = reverse("recipe:ingredient-list")
        cls.fake = Faker()

    def _ingredient_detail_url(self, ingredient_id: int) -> str:
        return reverse("recipe:ingredient-detail", args=[ingredient_id])

    def test_retrieve_ingredients(self) -> None:
        IngredientFactory.create_batch(2, user=self.user)

        res = self.api_client.get(self.ingredients_url)

        self.assertEqual(res.status_code, HTTPStatus.OK)

        ingredients = Ingredient.objects.all().order_by("-name")
        serializer = IngredientSerializer(ingredients, many=True)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self) -> None:
        user2 = UserFactory.create()
        IngredientFactory.create(user=user2)
        ingredient = IngredientFactory.create(user=self.user)

        res = self.api_client.get(self.ingredients_url)

        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0], IngredientSerializer(ingredient).data)

    def test_update_ingredient(self) -> None:
        ingredient = IngredientFactory.create(user=self.user)

        payload = {"name": self.fake.word()}
        url = self._ingredient_detail_url(ingredient.id)
        res = self.api_client.patch(url, payload)

        self.assertEqual(res.status_code, HTTPStatus.OK)
        expected = IngredientSerializer(ingredient).data | payload
        ingredient.refresh_from_db()
        actual = IngredientSerializer(ingredient).data
        self.assertEqual(actual, expected)

    def test_delete_ingredient(self) -> None:
        ingredient = IngredientFactory.create(user=self.user)

        url = self._ingredient_detail_url(ingredient.id)
        res = self.api_client.delete(url)

        self.assertEqual(res.status_code, HTTPStatus.NO_CONTENT)
        self.assertFalse(Ingredient.objects.filter(id=ingredient.id).exists())

    def test_filter_ingredients_assigned_to_recipes(self) -> None:
        ingredient1 = IngredientFactory.create(user=self.user)
        ingredient2 = IngredientFactory.create(user=self.user)
        recipe = RecipeFactory.create(user=self.user)
        recipe.ingredients.add(ingredient1)

        params = {"assigned_only": True}
        res = self.api_client.get(self.ingredients_url, params)

        s1 = IngredientSerializer(ingredient1)
        s2 = IngredientSerializer(ingredient2)

        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filter_ingredients_unique(self) -> None:
        ingredient = IngredientFactory.create(user=self.user)
        IngredientFactory.create(user=self.user)

        recipe1 = RecipeFactory.create(user=self.user)
        recipe2 = RecipeFactory.create(user=self.user)

        recipe1.ingredients.add(ingredient)
        recipe2.ingredients.add(ingredient)

        params = {"assigned_only": True}
        res = self.api_client.get(self.ingredients_url, params)

        self.assertEqual(len(res.data), 1)
