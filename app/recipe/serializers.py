from typing import Any

from core.models import Ingredient, Recipe, Tag
from django.db.models import Model
from rest_framework import serializers


class AbstractAttrSerializer[T: Model](serializers.ModelSerializer[T]):
    """Shared serializer for Tag and Ingredient."""

    class Meta:
        model: type[Model] | None = None  # overridden by subclasses
        fields = ["id", "name"]
        read_only_fields = ["id"]
        abstract = True  # tells DRF this class has no concrete model


class TagSerializer(AbstractAttrSerializer[Tag]):
    class Meta(AbstractAttrSerializer.Meta):
        model = Tag


class IngredientSerializer(AbstractAttrSerializer[Ingredient]):
    class Meta(AbstractAttrSerializer.Meta):
        model = Ingredient


# Serializers / Actions:
#   - RecipeSerializer        : list (GET /recipes/) & create/update (POST/PUT/PATCH)
#   - RecipeDetailSerializer  : retrieve (GET /recipes/{id}/)
#   - RecipeImageSerializer   : upload action (POST /recipes/{id}/upload-image/)
#
# +--------------+------------------+------------------------+-----------------------+
# | Field        | RecipeSerializer | RecipeDetailSerializer | RecipeImageSerializer |
# +--------------+------------------+------------------------+-----------------------+
# | id           | R                | R                      | R                     |
# | title        | RW               | RW                     | —                     |
# | time_minutes | RW               | RW                     | —                     |
# | price        | RW               | RW                     | —                     |
# | link         | RW               | RW                     | —                     |
# | description  | W                | R                      | —                     |
# | image        | —                | R                      | W                     |
# +--------------+------------------+------------------------+-----------------------+
#
# Legend: R = read-only, W = write-only, RW = read & write, — = not included


class RecipeSerializer(serializers.ModelSerializer[Recipe]):
    tags = TagSerializer(many=True, required=False)
    ingredients = IngredientSerializer(many=True, required=False)
    description = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Recipe
        fields = [
            "id",
            "title",
            "time_minutes",
            "price",
            "link",
            "tags",
            "ingredients",
            "description",
        ]
        read_only_fields = ["id"]

    def create(self, validated_data: dict[str, Any]) -> Recipe:
        tags: list[dict[str, Any]] = validated_data.pop("tags", [])
        ingredients: list[dict[str, Any]] = validated_data.pop("ingredients", [])
        recipe = Recipe.objects.create(**validated_data)
        self._get_or_create_tags(tags, recipe)
        self._get_or_create_ingredients(ingredients, recipe)

        return recipe

    def update(self, instance: Recipe, validated_data: dict[str, Any]) -> Recipe:
        tags: list[dict[str, Any]] | None = validated_data.pop("tags", None)
        ingredients: list[dict[str, Any]] | None = validated_data.pop("ingredients", None)
        if tags is not None:
            instance.tags.clear()
            self._get_or_create_tags(tags, instance)
        if ingredients is not None:
            instance.ingredients.clear()
            self._get_or_create_ingredients(ingredients, instance)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance

    def _get_or_create_tags(self, tags: list[dict[str, Any]], instance: Recipe) -> None:
        user = self.context["request"].user
        for tag in tags:
            tag_obj, _ = Tag.objects.get_or_create(user=user, **tag)
            instance.tags.add(tag_obj)

    def _get_or_create_ingredients(
        self, ingredients: list[dict[str, Any]], instance: Recipe
    ) -> None:
        user = self.context["request"].user
        for ingredient in ingredients:
            ingredient_obj, _ = Ingredient.objects.get_or_create(user=user, **ingredient)
            instance.ingredients.add(ingredient_obj)


class RecipeDetailSerializer(RecipeSerializer):
    description = serializers.CharField(read_only=True)
    image = serializers.ImageField(read_only=True)

    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ["image"]
        read_only_fields = RecipeSerializer.Meta.read_only_fields + ["image"]


# Separate serializer because it's best practice to upload one type of data to an API;
# we don't want the same API to accept form data as well as an image (multipart form).
class RecipeImageSerializer(serializers.ModelSerializer[Recipe]):
    class Meta:
        model = Recipe
        fields = ["id", "image"]
        read_only_fields = ["id"]
        extra_kwargs = {"image": {"required": True}}
