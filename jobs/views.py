import requests
from allauth.socialaccount.models import SocialAccount
from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from rest_framework.generics import UpdateAPIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework import generics, parsers, status
from django.contrib.auth import get_user_model
from .paginators import JobPagination
from .perms import *
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q, Count
from .serializers import *

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def to_representation(self, instance):
        data = super().to_representation(instance)

        if hasattr(instance, 'profile_picture') and instance.profile_picture:
            from cloudinary.utils import cloudinary_url
            url, options = cloudinary_url(instance.profile_picture.name, secure=True)
            data['profile_picture'] = url


        return data

    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


    @action(detail=False, methods=['post'], url_path='request-verification')
    def request_verification(self, request):
        user = request.user

        if user.is_verified:
            return Response({"detail": "Tài khoản đã được xác thực."}, status=400)

        if VerificationRequest.objects.filter(user=user, status='pending').exists():
            return Response({"detail": "Bạn đã gửi yêu cầu xác thực và đang chờ duyệt."}, status=400)

        VerificationRequest.objects.create(user=user)
        return Response({"detail": "Đã gửi yêu cầu xác thực thành công."}, status=201)


class AuthViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]
    @action(detail=False, methods=['post'])
    def register(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Đăng ký thành công!"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class JobViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Job.objects.filter(active=True)
    serializer_class = JobSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering_fields = ['created_date', 'salary', 'popularity']
    ordering = ['-created_date']
    pagination_class = JobPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.annotate(popularity=Count('application'))

        title = self.request.query_params.get('title')
        location = self.request.query_params.get('location')
        min_salary = self.request.query_params.get('min_salary')
        max_salary = self.request.query_params.get('max_salary')
        job_type = self.request.query_params.get('job_type')

        if title:
            queryset = queryset.filter(title__icontains=title)
        if location:
            queryset = queryset.filter(location__icontains=location)
        if min_salary:
            queryset = queryset.filter(salary__gte=min_salary)
        if max_salary:
            queryset = queryset.filter(salary__lte=max_salary)
        if job_type:
            queryset = queryset.filter(job_type__name__icontains=job_type)

        return queryset

    def retrieve(self, request, *args, **kwargs):
        job = self.get_object()

        if request.user.is_authenticated:
            already_viewed = JobView.objects.filter(job=job, viewer=request.user).exists()
            if not already_viewed:
                JobView.objects.create(job=job, viewer=request.user)

        serializer = self.get_serializer(job)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def search(self, request):
        queryset = self.get_queryset()
        queryset = self.filter_queryset(queryset)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = JobSearchSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = JobSearchSerializer(queryset, many=True)
        return Response(serializer.data)

class FavoriteJobViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        queryset = FavoriteJob.objects.filter(user=request.user)
        serializer = FavoriteJobSerializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        favorite = get_object_or_404(FavoriteJob, pk=pk, user=request.user)
        serializer = FavoriteJobSerializer(favorite)
        return Response(serializer.data)

    def create(self, request):
        serializer = FavoriteJobSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        favorite = get_object_or_404(FavoriteJob, pk=pk, user=request.user)
        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class EmJobViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsEmployer]

    def get_queryset(self):
        try:
            recruiter_profile = RecruiterProfile.objects.get(user=self.request.user)
            return Job.objects.filter(recruiter=recruiter_profile).prefetch_related('application_set')
        except RecruiterProfile.DoesNotExist:
            return Job.objects.none()

    def get_serializer_class(self):
        if self.action in ['applications']:
            return JobAnalyticsSerializer
        return JobStatsSerializer

    def perform_create(self, serializer):
        recruiter_profile = get_object_or_404(RecruiterProfile, user=self.request.user)
        serializer.save(recruiter=recruiter_profile, company=recruiter_profile.company)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        recruiter_profile = get_object_or_404(RecruiterProfile, user=self.request.user)
        serializer.save(recruiter=recruiter_profile, company=recruiter_profile.company)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="applications")
    def applications(self, request):
        recruiter_profile = get_object_or_404(RecruiterProfile, user=self.request.user)
        jobs = Job.objects.filter(recruiter=recruiter_profile).prefetch_related('application_set')
        serializer = self.get_serializer(jobs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="candidates")
    def job_applications(self, request, pk=None):
        job = get_object_or_404(Job, pk=pk, recruiter__user=request.user)
        applications = Application.objects.filter(job=job)
        serializer = ApplicantDetailSerializer(applications, many=True)
        return Response(serializer.data)


class GoogleLogin(APIView):
    def post(self, request, *args, **kwargs):
        google_token = request.data.get('access_token')

        if not google_token:
            return Response({'error': 'No token provided'}, status=status.HTTP_400_BAD_REQUEST)

        url = f"https://www.googleapis.com/oauth2/v3/tokeninfo?id_token={google_token}"
        response = requests.get(url)
        user_info = response.json()

        if 'error_description' in user_info:
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            social_account = SocialAccount.objects.get(uid=user_info['sub'], provider='google')
            user = social_account.user
        except SocialAccount.DoesNotExist:
            user = get_user_model().objects.create_user(
                username=user_info['email'],
                email=user_info['email'],
                first_name=user_info['given_name'],
                last_name=user_info['family_name'],
            )

        return Response({
            'user': {
                'username': user.username,
                'email': user.email,
            }
        })

class EmployerCompanyViewSet(viewsets.ViewSet, generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsEmployer]
    serializer_class = CompanySerializer

    def create(self, request):
        if RecruiterProfile.objects.filter(user=request.user).exists():
            return Response({"detail": "Bạn đã tạo công ty rồi."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        company = serializer.save()
        RecruiterProfile.objects.create(user=request.user, company=company)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get', 'put'], permission_classes=[permissions.IsAuthenticated, IsEmployer])
    def me(self, request):
        try:
            profile = RecruiterProfile.objects.get(user=request.user)
            company = profile.company
        except RecruiterProfile.DoesNotExist:
            return Response({"detail": "Bạn chưa có công ty."}, status=status.HTTP_404_NOT_FOUND)

        if request.method == 'GET':
            serializer = self.get_serializer(company)
            return Response(serializer.data)

        elif request.method == 'PUT':
            serializer = self.get_serializer(company, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

class JobTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = JobType.objects.all()
    serializer_class = JobTypeSerializer


class CVViewSet(viewsets.ModelViewSet):
    serializer_class = CVSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        # Chỉ lấy CV của chính user đang đăng nhập
        return CV.objects.filter(applicant=self.request.user, active=True)

    def perform_create(self, serializer):
        serializer.save(applicant=self.request.user)


class MyApplicationsAPIView(generics.ListAPIView):
    serializer_class = ApplicationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Application.objects.filter(applicant=self.request.user).select_related('job', 'job__company').order_by(
            '-created_date')


class ApplicationViewSet(viewsets.ModelViewSet):
    queryset = Application.objects.select_related(
        'applicant', 'job', 'cv'
    ).all()

    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['job', 'applicant', 'status']

    def get_serializer_class(self):
        if self.action == 'list':
            return ApplicationListSerializer2
        elif self.action == 'create':
            return ApplicationCreateSerializer
        return ApplicationSerializer2

    def get_queryset(self):
        user = self.request.user

        if user.role == User.EMPLOYER:
            recruiter = RecruiterProfile.objects.filter(user=user).first()
            if recruiter:
                return self.queryset.filter(job__recruiter=recruiter)
            return Application.objects.none()

        if user.role == User.JOB_SEEKER:
            return self.queryset.filter(applicant=user)

        return self.queryset

    def create(self, request, *args, **kwargs):
        if request.user.role != User.JOB_SEEKER:
            return Response(
                {"error": "Chỉ người tìm việc mới được phép ứng tuyển"},
                status=status.HTTP_403_FORBIDDEN
            )

        data = request.data.copy()
        data['applicant'] = request.user.id

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        allowed_fields = ['status', 'recruiter_notes']
        filtered_data = {k: v for k, v in request.data.items() if k in allowed_fields}
        application = self.get_object()

        request.data.clear()
        request.data.update(filtered_data)

        subject = f"Cập nhật trạng thái ứng tuyển - {application.job.title}"
        message = (
            f"Chào {application.applicant.username},\n\n"
            f"Trạng thái ứng tuyển của bạn cho vị trí {application.job.title} đã được cập nhật trạng thái mới.\n"
            f"Vui lòng kiểm tra chi tiết trên hệ thống.\n\n"
            f"Cảm ơn bạn đã sử dụng Hệ thống Tìm việc Online!"
        )
        send_mail(subject, message, settings.EMAIL_HOST_USER, [application.applicant.email])
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        application = self.get_object()
        user = request.user

        if (user.role == User.JOB_SEEKER and application.applicant == user) or user.role == User.ADMIN:
            return super().destroy(request, *args, **kwargs)

        return Response(
            {"error": "Bạn không có quyền xóa application này"},
            status=status.HTTP_403_FORBIDDEN
        )

    @action(detail=False, methods=['get'])
    def by_job_and_applicant(self, request):
        job_id = request.query_params.get('job')
        applicant_id = request.query_params.get('applicant')

        if not job_id or not applicant_id:
            return Response(
                {"error": "Cần cung cấp job và applicant parameters"},
                status=status.HTTP_400_BAD_REQUEST
            )

        application = self.get_queryset().filter(job_id=job_id, applicant_id=applicant_id).first()

        if application:
            serializer = self.get_serializer(application)
            return Response({
                "results": [serializer.data],
                "count": 1
            })

        return Response({"results": [], "count": 0})

    @action(detail=False, methods=['patch'])
    def by_job_applicant(self, request):
        job_id = request.query_params.get('job')
        applicant_id = request.query_params.get('applicant')

        if not job_id or not applicant_id:
            return Response(
                {"error": "Cần cung cấp job và applicant parameters"},
                status=status.HTTP_400_BAD_REQUEST
            )

        application = self.get_queryset().filter(job_id=job_id, applicant_id=applicant_id).first()

        if not application:
            return Response(
                {"error": "Không tìm thấy application với job và applicant đã cho"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(application, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            "message": "Cập nhật application thành công",
            "data": serializer.data
        })


class EmCVViewSet(viewsets.ReadOnlyModelViewSet):
   serializer_class = CVDetailSerializer
   permission_classes = [IsAuthenticated]
   queryset = CV.objects.all()



class InterviewViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        queryset = Interview.objects.all()
        serializer = InterviewSerializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        interview = get_object_or_404(Interview, pk=pk)
        serializer = InterviewSerializer(interview)
        return Response(serializer.data)

    def create(self, request):
        serializer = InterviewSerializer(data=request.data)
        if serializer.is_valid():
            interview = serializer.save()

            application = interview.application
            application.status = 'interview'
            application.save()

            to_email = application.applicant.email
            subject = "📅 Lịch phỏng vấn - " + application.job.title
            message = (
                f"Chào {application.applicant.username},\n\n"
                f"Bạn được mời phỏng vấn cho vị trí {application.job.title} tại {application.job.company.name}.\n"
                f"Thời gian: {interview.date.strftime('%H:%M %d/%m/%Y')}\n"
                f"Địa điểm: {interview.location or 'Online'}\n"
                f"{'Link phỏng vấn: ' + interview.link if interview.link else ''}\n\n"
                "Chúc bạn may mắn!\n-- Hệ thống Tìm việc Online --"
            )
            send_mail(subject, message, settings.EMAIL_HOST_USER, [to_email])

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminUserViewSet(viewsets.ModelViewSet):
    serializer_class = AdminUserSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        queryset = User.objects.all()
        role = self.request.query_params.get('role', None)
        search = self.request.query_params.get('search', None)
        is_active = self.request.query_params.get('is_active', None)

        if role and role != 'all':
            queryset = queryset.filter(role=role)

        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) | Q(email__icontains=search)
            )

        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active_bool)

        return queryset

    @action(detail=True, methods=['patch'])
    def toggle(self, request, pk=None):
        user = self.get_object()
        is_active = request.data.get('is_active')

        if is_active is not None:
            user.is_active = is_active
            user.save()

            return Response({
                'message': 'User status updated successfully',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'is_active': user.is_active
                }
            })

        return Response({'error': 'is_active field required'},
                        status=status.HTTP_400_BAD_REQUEST)


class AdminJobViewSet(viewsets.ModelViewSet):
    serializer_class = AdminJobSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        queryset = Job.objects.select_related('company', 'recruiter', 'job_type')
        search = self.request.query_params.get('search', None)
        active = self.request.query_params.get('active', None)
        company_id = self.request.query_params.get('company_id', None)
        job_type_id = self.request.query_params.get('job_type_id', None)

        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(company__name__icontains=search)
            )

        if active is not None:
            active_bool = active.lower() == 'true'
            queryset = queryset.filter(active=active_bool)

        if company_id:
            queryset = queryset.filter(company_id=company_id)

        if job_type_id:
            queryset = queryset.filter(job_type_id=job_type_id)

        return queryset

    @action(detail=True, methods=['patch'])
    def toggle(self, request, pk=None):
        job = self.get_object()
        active = request.data.get('active')

        if active is not None:
            job.active = active
            job.save()

            return Response({
                'message': 'Job status updated successfully',
                'job': {
                    'id': job.id,
                    'title': job.title,
                    'active': job.active
                }
            })

        return Response({'error': 'active field required'},
                        status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        job = self.get_object()
        job.delete()
        return Response({'message': 'Job deleted successfully'})


class AdminCompanyViewSet(viewsets.ModelViewSet):
    serializer_class = AdminCompanySerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        queryset = Company.objects.all()
        search = self.request.query_params.get('search', None)
        verified = self.request.query_params.get('verified', None)

        if search:
            queryset = queryset.filter(name__icontains=search)

        if verified is not None:
            verified_bool = verified.lower() == 'true'
            if verified_bool:
                queryset = queryset.filter(
                    recruiterprofile__user__is_verified=True
                ).distinct()

        return queryset


class AdminApplicationViewSet(viewsets.ModelViewSet):
    serializer_class = AdminApplicationSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        queryset = Application.objects.select_related('job', 'applicant', 'cv')
        status_filter = self.request.query_params.get('status', None)
        job_id = self.request.query_params.get('job_id', None)
        applicant_id = self.request.query_params.get('applicant_id', None)

        if status_filter:
            queryset = queryset.filter(status=status_filter)

        if job_id:
            queryset = queryset.filter(job_id=job_id)

        if applicant_id:
            queryset = queryset.filter(applicant_id=applicant_id)

        return queryset


class AdminVerificationViewSet(viewsets.ModelViewSet):
    serializer_class = AdminVerificationSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        queryset = VerificationRequest.objects.select_related('user')
        status_filter = self.request.query_params.get('status', None)

        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset

    def partial_update(self, request, *args, **kwargs):
        verification = self.get_object()
        status_value = request.data.get('status')

        if status_value:
            verification.status = status_value
            verification.save()

            if status_value == 'approved':
                verification.user.is_verified = True
                subject = "Xác thực tài khoản nhà tuyển dụng - Thành công"
                message = (
                    f"Chào {verification.user.username},\n\n"
                    f"Yêu cầu xác thực tài khoản nhà tuyển dụng của bạn đã được phê duyệt.\n"
                    f"Bạn có thể bắt đầu đăng tuyển công việc trên hệ thống."
                )
            elif status_value == 'rejected':
                verification.user.is_verified = False
                subject = "Xác thực tài khoản nhà tuyển dụng - Từ chối"
                message = (
                    f"Chào {verification.user.username},\n\n"
                    f"Yêu cầu xác thực tài khoản nhà tuyển dụng của bạn đã bị từ chối.\n"
                    f"Vui lòng liên hệ admin để biết thêm chi tiết."
                )

            verification.user.save()
            send_mail(subject, message, settings.EMAIL_HOST_USER, [verification.user.email])

            return Response({
                'message': 'Verification request updated successfully',
                'verification': {
                    'id': verification.id,
                    'status': verification.status,
                    'updated_date': verification.updated_date
                }
            })

        return Response({'error': 'status field required'},
                        status=status.HTTP_400_BAD_REQUEST)


class AdminDashboardView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        total_users = User.objects.count()
        total_jobs = Job.objects.count()
        total_companies = Company.objects.count()
        pending_verifications = VerificationRequest.objects.filter(status='pending').count()
        total_applications = Application.objects.count()


        data = {
            'totalUsers': total_users,
            'totalJobs': total_jobs,
            'totalCompanies': total_companies,
            'pendingVerifications': pending_verifications,
            'totalApplications': total_applications,
        }

        return Response(data)
