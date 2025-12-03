from http import HTTPStatus

from core.models import Tag
from core.models import User as CustomUser
from core.tests.factories import RecipeFactory, TagFactory, UserFactory
from django.test import TestCase
from django.urls import reverse
from faker import Faker
from rest_framework.test import APIClient

from recipe.serializers import TagSerializer


class PublicTagsAPITests(TestCase):
    api_client: APIClient
    tags_url: str

    @classmethod
    def setUpTestData(cls: type[PublicTagsAPITests]) -> None:
        cls.api_client = APIClient()
        cls.tags_url = reverse("recipe:tag-list")

    def test_auth_required(self) -> None:
        res = self.api_client.get(self.tags_url)

        self.assertEqual(res.status_code, HTTPStatus.UNAUTHORIZED)


class PrivateTagsAPITests(TestCase):
    api_client: APIClient
    tags_url: str
    user: CustomUser
    fake: Faker

    @classmethod
    def setUpTestData(cls: type[PrivateTagsAPITests]) -> None:
        cls.api_client = APIClient()
        cls.user = UserFactory.create()
        cls.api_client.force_authenticate(cls.user)
        cls.tags_url = reverse("recipe:tag-list")
        cls.fake = Faker()

    def _tag_detail_url(self, tag_id: int) -> str:
        return reverse("recipe:tag-detail", args=[tag_id])

    def test_retrieve_tags(self) -> None:
        TagFactory.create_batch(2, user=self.user)

        res = self.api_client.get(self.tags_url)

        self.assertEqual(res.status_code, HTTPStatus.OK)

        tags = Tag.objects.all().order_by("-name")
        serializer = TagSerializer(tags, many=True)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self) -> None:
        user2 = UserFactory.create()
        TagFactory.create(user=user2)
        tag = TagFactory.create(user=self.user)

        res = self.api_client.get(self.tags_url)

        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0], TagSerializer(tag).data)

    def test_update_tag(self) -> None:
        tag = TagFactory.create(user=self.user)

        payload = {"name": self.fake.word()}
        url = self._tag_detail_url(tag.id)
        res = self.api_client.patch(url, payload)

        self.assertEqual(res.status_code, HTTPStatus.OK)
        expected = TagSerializer(tag).data | payload
        tag.refresh_from_db()
        actual = TagSerializer(tag).data
        self.assertEqual(actual, expected)

    def test_delete_tag(self) -> None:
        tag = TagFactory.create(user=self.user)

        url = self._tag_detail_url(tag.id)
        res = self.api_client.delete(url)

        self.assertEqual(res.status_code, HTTPStatus.NO_CONTENT)
        self.assertFalse(Tag.objects.filter(id=tag.id).exists())

    def test_filter_tags_assigned_to_recipes(self) -> None:
        tag1 = TagFactory.create(user=self.user)
        tag2 = TagFactory.create(user=self.user)
        recipe = RecipeFactory.create(user=self.user)
        recipe.tags.add(tag1)

        params = {"assigned_only": True}
        res = self.api_client.get(self.tags_url, params)

        s1 = TagSerializer(tag1)
        s2 = TagSerializer(tag2)

        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filter_tags_unique(self) -> None:
        tag = TagFactory.create(user=self.user)
        TagFactory.create(user=self.user)

        recipe1 = RecipeFactory.create(user=self.user)
        recipe2 = RecipeFactory.create(user=self.user)

        recipe1.tags.add(tag)
        recipe2.tags.add(tag)

        params = {"assigned_only": True}
        res = self.api_client.get(self.tags_url, params)

        self.assertEqual(len(res.data), 1)
