from typing import cast

from core.models import User as CustomUser
from rest_framework import generics
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import BrowsableAPIRenderer, JSONRenderer

from user.serializers import AuthTokenSerializer, UserSerializer


class CreateUserView(generics.CreateAPIView[CustomUser]):
    serializer_class = UserSerializer


class CreateTokenView(ObtainAuthToken):
    serializer_class = AuthTokenSerializer
    # Enable the browsable API.
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]


class ManageUserView(generics.RetrieveUpdateAPIView[CustomUser]):
    serializer_class = UserSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self) -> CustomUser:
        # self.request.user can be either an authenticated User or an AnonymousUser.
        # Since we have IsAuthenticated permission, you know it's always a User, but
        # mypy doesn't.
        return cast(CustomUser, self.request.user)
