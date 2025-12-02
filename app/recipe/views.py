from typing import cast

from core.models import Recipe, Tag
from core.models import User as CustomUser
from django.db.models import QuerySet
from rest_framework import mixins, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.serializers import BaseSerializer

from .serializers import RecipeDetailSerializer, RecipeSerializer, TagSerializer


class RecipeViewSet(viewsets.ModelViewSet[Recipe]):
    serializer_class = RecipeDetailSerializer
    queryset = Recipe.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[Recipe]:
        return self.queryset.filter(user=cast(CustomUser, self.request.user)).order_by("-id")

    def get_serializer_class(self) -> type[RecipeSerializer]:
        if self.action == "list":
            return RecipeSerializer
        return self.serializer_class

    def perform_create(self, serializer: BaseSerializer[Recipe]) -> None:
        serializer.save(user=self.request.user)


# Mixins must be declared before GenericViewSet
class TagViewSet(
    mixins.DestroyModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet[Tag],
):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[Tag]:
        return self.queryset.filter(user=cast(CustomUser, self.request.user)).order_by("-name")
