from abc import ABC, abstractmethod
from typing import cast

from core.models import Ingredient, Recipe, Tag
from core.models import User as CustomUser
from django.db.models import Model, QuerySet
from rest_framework import mixins, status, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer, ModelSerializer

from .serializers import (
    IngredientSerializer,
    RecipeDetailSerializer,
    RecipeImageSerializer,
    RecipeSerializer,
    TagSerializer,
)


class RecipeViewSet(viewsets.ModelViewSet[Recipe]):
    serializer_class = RecipeSerializer
    queryset = Recipe.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[Recipe]:
        return self.queryset.filter(user=cast(CustomUser, self.request.user)).order_by("-id")

    def get_serializer_class(self) -> type[ModelSerializer[Recipe]]:
        if self.action == "retrieve":
            return RecipeDetailSerializer
        if self.action == "upload_image":
            return RecipeImageSerializer
        return self.serializer_class

    def perform_create(self, serializer: BaseSerializer[Recipe]) -> None:
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"], url_path="upload-image")
    def upload_image(self, request: Request, pk: str | None = None) -> Response:
        recipe = self.get_object()
        serializer = self.get_serializer(recipe, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BaseRecipeAttrViewSet[T: Model](
    mixins.DestroyModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet[T],
    ABC,
):
    """Abstract base class for Tag and Ingredient attribute viewsets."""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    # DRF defines .queryset as a class attribute that may be None.
    # Force subclasses to provide a queryset.
    # Base:
    # - queryset is a method wrapped as a property, not a real attribute.
    # - It returns QuerySet[T].
    #
    # Subclass:
    # - queryset is a class-level variable, not a property.
    #
    # Mypy considers this an override mismatch, so, we suppress the violation.
    @property
    @abstractmethod
    def queryset(self) -> QuerySet[T]:  # type: ignore[override]
        pass

    def get_queryset(self) -> QuerySet[T]:
        qs = self.queryset  # mypy now knows it's a QuerySet[T]
        user = cast(CustomUser, self.request.user)
        return qs.filter(user=user).order_by("-name")


# Mixins must be declared before GenericViewSet
class TagViewSet(BaseRecipeAttrViewSet[Tag]):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()


class IngredientViewSet(BaseRecipeAttrViewSet[Ingredient]):
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
