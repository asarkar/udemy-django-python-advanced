from typing import Any

from core.models import Recipe, Tag
from rest_framework import serializers


class TagSerializer(serializers.ModelSerializer[Tag]):
    class Meta:
        model = Tag
        fields = ["id", "name"]
        read_only_fields = ["id"]


class RecipeSerializer(serializers.ModelSerializer[Recipe]):
    tags = TagSerializer(many=True, required=False)

    class Meta:
        model = Recipe
        fields = ["id", "title", "time_minutes", "price", "link", "tags"]
        read_only_fields = ["id"]

    def create(self, validated_data: dict[str, Any]) -> Recipe:
        tags: list[dict[str, Any]] = validated_data.pop("tags", [])
        recipe = Recipe.objects.create(**validated_data)
        self._get_or_create_tags(tags, recipe)

        return recipe

    def update(self, instance: Recipe, validated_data: dict[str, Any]) -> Recipe:
        tags: list[dict[str, Any]] | None = validated_data.pop("tags", None)
        if tags is not None:
            instance.tags.clear()
            self._get_or_create_tags(tags, instance)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance

    def _get_or_create_tags(self, tags: list[dict[str, Any]], instance: Recipe) -> None:
        user = self.context["request"].user
        for tag in tags:
            tag_obj, _ = Tag.objects.get_or_create(user=user, **tag)
            instance.tags.add(tag_obj)


class RecipeDetailSerializer(RecipeSerializer):
    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ["description"]
