from oauth2_provider.views import RevokeTokenView
from rest_framework import routers
from django.urls import path, include
from . import views
from .views import UserViewSet, AuthViewSet, EmployerVerificationViewSet

router = routers.DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'employers', EmployerVerificationViewSet, basename='employers')
router.register(r'auth', AuthViewSet, basename='auth')


urlpatterns = [
    path('', include(router.urls)),
    path('o/revoke_token/', RevokeTokenView.as_view(), name='revoke-token'),
]