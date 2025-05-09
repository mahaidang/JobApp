from oauth2_provider.views import RevokeTokenView
from rest_framework import routers
from django.urls import path, include
from . import views
from .views import UserViewSet, AuthViewSet, EmployerVerificationViewSet, CVViewSet, ApplyJobAPIView, MyApplicationsAPIView, UpdateApplicationStatusAPIView, FirebaseTokenAPIView
from rest_framework.routers import DefaultRouter

router = routers.DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'employers', EmployerVerificationViewSet, basename='employers')
router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'cvs', CVViewSet, basename='cv')


urlpatterns = [
    path('', include(router.urls)),
    path('api/', include(router.urls)),
    path('o/', include('oauth2_provider.urls',namespace='oauth2_provider')),
    path('apply-job/<int:job_id>/', ApplyJobAPIView.as_view(), name='apply-job'),
    path('my-applications/', MyApplicationsAPIView.as_view(), name='my-applications'),
    path('update-application-status/<int:pk>/', UpdateApplicationStatusAPIView.as_view(), name='update-application-status'),
    path('firebase-token/', FirebaseTokenAPIView.as_view(), name='firebase-token'),
]


