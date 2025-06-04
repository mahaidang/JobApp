from oauth2_provider.views import RevokeTokenView
from rest_framework import routers
from django.urls import path, include
from . import views
from .views import *

router = routers.DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'jobs', JobViewSet, basename='job')
router.register(r'job-types', JobTypeViewSet, basename='job-type')
router.register(r'cvs', CVViewSet, basename='cv')
router.register(r'em-company', EmployerCompanyViewSet, basename='em-company')
router.register(r'employer/jobs', EmJobViewSet, basename='employer-jobs')
router.register(r'favorite-jobs', FavoriteJobViewSet, basename='favorite-job')
router.register(r'applications', ApplicationViewSet, basename='application')
router.register(r'em-cvs', EmCVViewSet, basename='em-cv')
router.register(r'interviews', InterviewViewSet, basename='interview')
router.register(r'ad-users', AdminUserViewSet, basename='admin-users')
router.register(r'ad-jobs', AdminJobViewSet, basename='admin-jobs')
router.register(r'ad-companies', AdminCompanyViewSet, basename='admin-companies')
router.register(r'ad-applications', AdminApplicationViewSet, basename='admin-applications')
router.register(r'ad-verifications', AdminVerificationViewSet, basename='admin-verifications')



urlpatterns = [
    path('', include(router.urls)),
    path('o/revoke_token/', RevokeTokenView.as_view(), name='revoke-token'),
    path('auth/google/', GoogleLogin.as_view(), name='google-login'),
    path('o/', include('oauth2_provider.urls',namespace='oauth2_provider')),
    path('my-applications/', MyApplicationsAPIView.as_view(), name='my-applications'),
    path('stats/', AdminDashboardView.as_view(), name='admin-stats'),
    # path('dashboard-charts/', AdminDashboardChartsView.as_view(), name='admin-dashboard-charts'),

]