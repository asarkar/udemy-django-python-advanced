from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as translate

from .models import Ingredient, Recipe, Tag, User


class UserAdmin(BaseUserAdmin):  # type: ignore[type-arg]
    ordering = ["id"]
    list_display = ["email", "name"]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (translate("Permissions"), {"fields": ("is_active", "is_staff", "is_superuser")}),
        (translate("Important dates"), {"fields": ("last_login",)}),
    )
    readonly_fields = ["last_login"]
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                ),
            },
        ),
    )


admin.site.register(User, UserAdmin)
admin.site.register(Recipe)
admin.site.register(Tag)
admin.site.register(Ingredient)
