from __future__ import annotations

from typing import Any

from core.models import User as CustomUser
from django.contrib.auth import authenticate, get_user_model
from django.utils.translation import gettext_lazy as translate
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer[CustomUser]):
    class Meta:
        model = User
        fields = ["email", "password", "name"]
        extra_kwargs = {"password": {"write_only": True, "min_length": 5}}

    def create(self, validated_data: dict[str, Any]) -> CustomUser:
        return User.objects.create_user(**validated_data)

    def update(self, instance: CustomUser, validated_data: dict[str, Any]) -> CustomUser:
        password = validated_data.pop("password", None)
        user = super().update(instance, validated_data)

        if password:
            user.set_password(password)
            user.save()

        return user


class AuthTokenSerializer(serializers.Serializer[Any]):
    email = serializers.EmailField()
    password = serializers.CharField(
        style={"input_type": "password"},
        trim_whitespace=False,
    )

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        email = attrs.get("email")
        password = attrs.get("password")
        user = authenticate(
            request=self.context.get("request"),
            username=email,
            password=password,
        )
        if user is None:
            msg = translate("Unable to authenticate with provided credentials.")
            raise serializers.ValidationError(msg, code="authorization")

        attrs["user"] = user
        return attrs
