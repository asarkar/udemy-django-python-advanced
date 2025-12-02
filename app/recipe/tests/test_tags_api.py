from http import HTTPStatus

from core.models import Tag
from core.models import User as CustomUser
from core.tests.factories import TagFactory, UserFactory
from django.test import TestCase
from django.urls import reverse
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


def tag_detail_url(tag_id: int) -> str:
    return reverse("recipe:tag-detail", args=[tag_id])


class PrivateTagsAPITests(TestCase):
    api_client: APIClient
    tags_url: str
    user: CustomUser

    @classmethod
    def setUpTestData(cls: type[PrivateTagsAPITests]) -> None:
        cls.api_client = APIClient()
        cls.user = UserFactory.create()
        cls.api_client.force_authenticate(cls.user)
        cls.tags_url = reverse("recipe:tag-list")

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

        payload = {"name": "Dessert"}
        url = tag_detail_url(tag.id)
        res = self.api_client.patch(url, payload)

        self.assertEqual(res.status_code, HTTPStatus.OK)
        expected = TagSerializer(tag).data | payload
        tag.refresh_from_db()
        actual = TagSerializer(tag).data
        self.assertEqual(actual, expected)

    def test_delete_tag(self) -> None:
        tag = TagFactory.create(user=self.user)

        url = tag_detail_url(tag.id)
        res = self.api_client.delete(url)

        self.assertEqual(res.status_code, HTTPStatus.NO_CONTENT)
        self.assertFalse(Tag.objects.filter(id=tag.id).exists())
