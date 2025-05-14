import requests
from allauth.socialaccount.models import SocialAccount
from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Count
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.generics import UpdateAPIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from rest_framework import viewsets, generics, parsers, permissions, status, filters
from django.contrib.auth import get_user_model, authenticate
from rest_framework.views import APIView

from .filters import JobFilter
from .firebase import send_multicast_notification, send_push_notification
from .models import Job, DeviceToken, Interview, Application, RecruiterProfile, CVView, CVSaveAction, CV, Notification
from .paginators import JobPagination
from .perms import IsEmployer, IsJobSeeker, IsOwnerOrReadOnly
from .serializers import UserRegisterSerializer, UserSerializer, EmployerVerificationSerializer, DeviceTokenSerializer, \
    JobSerializer, CVSerializer, ApplicationSerializer, ApplicationStatusUpdateSerializer

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def me(self, request):
        return Response({
            "id": request.user.id,
            "username": request.user.username,
            "email": request.user.email
        })

class AuthViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]
    @action(detail=False, methods=['post'])
    def register(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Đăng ký thành công!"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmployerVerificationViewSet(viewsets.ModelViewSet):
    """Admin xác thực Nhà tuyển dụng"""
    queryset = User.objects.filter(role=User.EMPLOYER)
    serializer_class = EmployerVerificationSerializer
    permission_classes = [permissions.IsAdminUser]  # Chỉ Admin mới có quyền duyệt

    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """Xác thực Nhà tuyển dụng"""
        employer = self.get_object()
        employer.is_verified = True
        employer.save()
        return Response({"message": "Nhà tuyển dụng đã được xác thực!"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Từ chối Nhà tuyển dụng"""
        employer = self.get_object()
        employer.is_verified = False
        employer.save()
        return Response({"message": "Nhà tuyển dụng đã bị từ chối!"}, status=status.HTTP_200_OK)


class DeviceTokenViewSet(viewsets.ModelViewSet):
    """Quản lý token thiết bị cho push notification"""
    serializer_class = DeviceTokenSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return DeviceToken.objects.filter(user=self.request.user, active=True)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            instance.active = False
            instance.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class NotificationViewSet(viewsets.ViewSet):
    """ViewSet tổng hợp các API thông báo"""

    permission_classes_by_action = {
        'send_push_notification': [IsAdminUser],
        'send_multicast_notification': [IsAdminUser],
        'send_new_job_notification': [IsAuthenticated],
        'send_interview_email': [IsAuthenticated],
    }

    def get_permissions(self):
        try:
            return [permission() for permission in self.permission_classes_by_action[self.action]]
        except (KeyError, AttributeError):
            return [IsAuthenticated()]

    @action(detail=False, methods=['post'], url_path='send-push-notification')
    def send_push_notification(self, request):
        token = request.data.get('token')
        title = request.data.get('title')
        body = request.data.get('body')
        data = request.data.get('data', {})

        if not token or not title or not body:
            return Response({'error': 'Token, title và body là bắt buộc'}, status=status.HTTP_400_BAD_REQUEST)

        result = send_push_notification(token, title, body, data)
        return Response(result, status=status.HTTP_200_OK if result.get('success') else status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='send-multicast-notification')
    def send_multicast_notification(self, request):
        user_ids = request.data.get('user_ids', [])
        title = request.data.get('title')
        body = request.data.get('body')
        data = request.data.get('data', {})

        if not title or not body:
            return Response({'error': 'Title và body là bắt buộc'}, status=status.HTTP_400_BAD_REQUEST)

        devices = DeviceToken.objects.filter(active=True)
        if user_ids:
            devices = devices.filter(user_id__in=user_ids)
        tokens = list(devices.values_list('token', flat=True))

        if not tokens:
            return Response({'message': 'Không tìm thấy token thiết bị nào'}, status=status.HTTP_404_NOT_FOUND)

        result = send_multicast_notification(tokens, title, body, data)
        return Response(result, status=status.HTTP_200_OK if result.get('success') else status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='send-new-job-notification')
    def send_new_job_notification(self, request):
        from .models import Job  # tránh circular import

        job_id = request.data.get('job_id')
        try:
            job = Job.objects.get(id=job_id)
        except Job.DoesNotExist:
            return Response({'error': 'Không tìm thấy việc làm'}, status=status.HTTP_404_NOT_FOUND)

        if not request.user.is_staff and (not hasattr(request.user, 'recruiterprofile') or request.user.recruiterprofile != job.recruiter):
            return Response({'error': 'Bạn không có quyền gửi thông báo cho việc làm này'}, status=status.HTTP_403_FORBIDDEN)

        title = "Việc làm mới!"
        body = f"{job.title} - {job.company.name}"
        data = {'job_id': str(job.id), 'notification_type': 'new_job'}

        tokens = list(DeviceToken.objects.filter(user__role='job_seeker', active=True).values_list('token', flat=True))

        if not tokens:
            return Response({'message': 'Không tìm thấy thiết bị nào để gửi thông báo'}, status=status.HTTP_404_NOT_FOUND)

        result = send_multicast_notification(tokens, title, body, data)
        if result.get('success'):
            return Response({
                'message': f'Đã gửi thông báo đến {result["success_count"]} thiết bị',
                'success_count': result['success_count'],
                'failure_count': result['failure_count']
            }, status=status.HTTP_200_OK)
        return Response({'error': result.get('error')}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], url_path='send-email/interview')
    def send_interview_email(self, request, pk=None):
        try:
            application = Application.objects.get(id=pk)
            interview = Interview.objects.get(application=application)
        except (Application.DoesNotExist, Interview.DoesNotExist):
            return Response({'error': 'Không tìm thấy hồ sơ hoặc lịch phỏng vấn.'}, status=status.HTTP_404_NOT_FOUND)

        to_email = application.applicant.email
        subject = "📅 Lịch phỏng vấn - " + application.job.title
        message = (
            f"Chào {application.applicant.username},\n\n"
            f"Bạn được mời phỏng vấn cho vị trí {application.job.title}.\n"
            f"Thời gian: {interview.date.strftime('%H:%M %d/%m/%Y')}\n"
            f"Địa điểm: {interview.location or 'Online'}\n"
            f"{'Link phỏng vấn: ' + interview.link if interview.link else ''}\n\n"
            "Chúc bạn may mắn!\n-- Hệ thống Tìm việc Online --"
        )

        send_mail(subject, message, settings.EMAIL_HOST_USER, [to_email])
        return Response({'message': 'Đã gửi email lịch phỏng vấn thành công.'})


class JobViewSet(viewsets.ModelViewSet):
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering_fields = ['created_date', 'salary', 'popularity']
    ordering = ['-created_date']

    def get_queryset(self):
        # Lấy queryset từ lớp cha trước
        queryset = super().get_queryset()

        # Thêm trường popularity để có thể sắp xếp
        queryset = queryset.annotate(popularity=Count('application'))
        title = self.request.query_params.get('title', None)
        location = self.request.query_params.get('location', None)
        min_salary = self.request.query_params.get('min_salary', None)
        max_salary = self.request.query_params.get('max_salary', None)
        job_type = self.request.query_params.get('job_type', None)

        # Tìm kiếm theo tiêu chí
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

    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Tìm kiếm công việc theo các tiêu chí như title, location, salary, job type.
        """
        queryset = self.get_queryset()
        queryset = self.filter_queryset(queryset)
        serializer = JobSerializer(queryset, many=True)
        return Response(serializer.data)


class EmployerApplicationStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            if user.role != 'employer':
                return Response({"detail": "Chỉ nhà tuyển dụng mới được xem thống kê."}, status=403)

            recruiter = RecruiterProfile.objects.get(user=user)
            jobs = recruiter.job_set.all()

            total_apps = Application.objects.filter(job__in=jobs).count()
            accepted_apps = Application.objects.filter(job__in=jobs, status='accepted').count()

            rate = (accepted_apps / total_apps * 100) if total_apps > 0 else 0

            return Response({
                "total_applications": total_apps,
                "accepted_applications": accepted_apps,
                "acceptance_rate": f"{rate:.1f}%"
            })
        except RecruiterProfile.DoesNotExist:
            return Response({"detail": "Không tìm thấy hồ sơ nhà tuyển dụng."}, status=404)


class RecruiterApplicationStatsViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, IsEmployer]

    @action(detail=False, methods=['get'], url_path='stats')
    def get_stats(self, request):
        try:
            recruiter_profile = RecruiterProfile.objects.get(user=request.user)
            jobs = Job.objects.filter(recruiter=recruiter_profile)
            total_applications = Application.objects.filter(job__in=jobs).count()
            qualified_candidates = Application.objects.filter(
                job__in=jobs, status__in=['interview', 'accepted']
            ).count()

            qualification_ratio = (qualified_candidates / total_applications) * 100 if total_applications > 0 else 0

            job_statistics = []
            for job in jobs:
                job_apps = Application.objects.filter(job=job)
                count = job_apps.count()
                qualified = job_apps.filter(status__in=['interview', 'accepted']).count()
                ratio = (qualified / count) * 100 if count > 0 else 0
                job_statistics.append({
                    'id': job.id,
                    'title': job.title,
                    'application_count': count,
                    'qualified_count': qualified,
                    'qualification_ratio': round(ratio, 2)
                })

            status_statistics = {}
            for code, name in Application.STATUS_CHOICES:
                status_statistics[code] = Application.objects.filter(job__in=jobs, status=code).count()

            return Response({
                'total_applications': total_applications,
                'qualified_candidates': qualified_candidates,
                'qualification_ratio': round(qualification_ratio, 2),
                'job_statistics': job_statistics,
                'status_statistics': status_statistics
            }, status=status.HTTP_200_OK)

        except RecruiterProfile.DoesNotExist:
            return Response({'error': 'User is not a recruiter'}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class JobSeekerProfileViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, IsJobSeeker]

    @action(detail=False, methods=['get'], url_path='stats')
    def get_stats(self, request):
        try:
            user = request.user
            user_applications = Application.objects.filter(applicant=user)
            cv_with_applications = user_applications.values_list('cv_id', flat=True).distinct()
            user_cvs = CV.objects.filter(id__in=cv_with_applications)

            if not user_cvs.exists():
                return Response({
                    "message": "You don't have any CVs submitted in applications yet."
                }, status=status.HTTP_200_OK)

            total_views = CVView.objects.filter(cv__in=user_cvs).count()
            total_saves = CVSaveAction.objects.filter(cv__in=user_cvs).count()
            total_responses = user_applications.filter(
                status__in=['reviewed', 'interview', 'accepted', 'rejected']
            ).count()

            response_rate = (total_responses / total_views * 100) if total_views > 0 else 0

            cv_statistics = []
            for cv in user_cvs:
                cv_views = CVView.objects.filter(cv=cv).count()
                cv_saves = CVSaveAction.objects.filter(cv=cv).count()
                cv_applications = user_applications.filter(cv=cv)
                cv_responses = cv_applications.filter(
                    status__in=['reviewed', 'interview', 'accepted', 'rejected']
                ).count()
                cv_response_rate = (cv_responses / cv_views * 100) if cv_views > 0 else 0

                response_stats = {
                    'pending': cv_applications.filter(status='pending').count(),
                    'reviewed': cv_applications.filter(status='reviewed').count(),
                    'interview': cv_applications.filter(status='interview').count(),
                    'accepted': cv_applications.filter(status='accepted').count(),
                    'rejected': cv_applications.filter(status='rejected').count(),
                    'saved': cv_saves
                }

                cv_statistics.append({
                    'id': cv.id,
                    'title': cv.title,
                    'views': cv_views,
                    'responses': cv_responses,
                    'response_rate': round(cv_response_rate, 2),
                    'response_stats': response_stats
                })

            application_stats = {
                'total': user_applications.count(),
                'pending': user_applications.filter(status='pending').count(),
                'reviewed': user_applications.filter(status='reviewed').count(),
                'interview': user_applications.filter(status='interview').count(),
                'accepted': user_applications.filter(status='accepted').count(),
                'rejected': user_applications.filter(status='rejected').count(),
            }

            successful = application_stats['interview'] + application_stats['accepted']
            application_success_rate = (successful / application_stats['total'] * 100) if application_stats['total'] > 0 else 0

            return Response({
                'total_cv_views': total_views,
                'total_responses': total_responses,
                'total_saves': total_saves,
                'response_rate': round(response_rate, 2),
                'cv_statistics': cv_statistics,
                'application_statistics': application_stats,
                'application_success_rate': round(application_success_rate, 2)
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CVInteractionViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, IsEmployer]

    @action(detail=True, methods=['post'], url_path='track-view')
    def track_view(self, request, pk=None):
        try:
            cv = get_object_or_404(CV, id=pk)
            recruiter_profile = get_object_or_404(RecruiterProfile, user=request.user)

            cv_view, created = CVView.objects.get_or_create(
                cv=cv,
                viewer=recruiter_profile,
                defaults={'active': True}
            )

            if not created and not cv_view.active:
                cv_view.active = True
                cv_view.save()

            return Response({
                'message': 'CV view tracked successfully',
                'cv_id': cv.id,
                'cv_title': cv.title,
                'created': created
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], url_path='save')
    def save_cv(self, request, pk=None):
        try:
            cv = get_object_or_404(CV, id=pk)
            recruiter_profile = get_object_or_404(RecruiterProfile, user=request.user)

            save_action, created = CVSaveAction.objects.get_or_create(
                cv=cv,
                recruiter=recruiter_profile,
                defaults={
                    'notes': request.data.get('notes', ''),
                    'active': True
                }
            )

            if not created:
                if 'notes' in request.data:
                    save_action.notes = request.data['notes']
                if not save_action.active:
                    save_action.active = True
                save_action.save()

            if created:
                CVView.objects.get_or_create(
                    cv=cv,
                    viewer=recruiter_profile,
                    defaults={'active': True}
                )

            return Response({
                'message': 'CV saved successfully',
                'cv_id': cv.id,
                'cv_title': cv.title,
                'created': created
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GoogleLogin(APIView):
    def post(self, request, *args, **kwargs):
        google_token = request.data.get('access_token')

        if not google_token:
            return Response({'error': 'No token provided'}, status=status.HTTP_400_BAD_REQUEST)

        # Xác thực token với Google
        url = f"https://www.googleapis.com/oauth2/v3/tokeninfo?id_token={google_token}"
        response = requests.get(url)
        user_info = response.json()

        if 'error_description' in user_info:
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)

        # Kiểm tra người dùng trong database
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

        # Trả về user thông qua API hoặc tạo token mới
        # Để tạo token JWT hoặc trả về thông tin người dùng
        return Response({
            'user': {
                'username': user.username,
                'email': user.email,
            }
        })

##an nguyễn
class CVViewSet(viewsets.ModelViewSet):
    serializer_class = CVSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        # Chỉ lấy CV của chính user đang đăng nhập
        return CV.objects.filter(applicant=self.request.user, active=True)

    def perform_create(self, serializer):
        serializer.save(applicant=self.request.user)


class ApplyJobAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, job_id):
        user = request.user

        try:
            job = Job.objects.get(pk=job_id)
        except Job.DoesNotExist:
            return Response({'detail': 'Công việc không tồn tại.'}, status=status.HTTP_404_NOT_FOUND)

        # Kiểm tra đã ứng tuyển chưa
        if Application.objects.filter(job=job, applicant=user).exists():
            return Response({'detail': 'Bạn đã ứng tuyển công việc này rồi.'}, status=status.HTTP_400_BAD_REQUEST)

        # Kiểm tra có CV chưa
        cv_id = request.data.get('cv_id')
        if not cv_id:
            return Response({'detail': 'Bạn cần chọn CV để ứng tuyển.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            cv = CV.objects.get(pk=cv_id, applicant=user)
        except CV.DoesNotExist:
            return Response({'detail': 'CV không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)

        application = Application.objects.create(
            job=job,
            applicant=user,
            cv=cv
        )

        serializer = ApplicationSerializer(application)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MyApplicationsAPIView(generics.ListAPIView):
    serializer_class = ApplicationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Application.objects.filter(applicant=self.request.user).select_related('job', 'job__company').order_by(
            '-created_date')


class IsRecruiterOfApplication(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Chỉ recruiter của công việc mới được phép update
        return obj.job.recruiter.user == request.user


class UpdateApplicationStatusAPIView(UpdateAPIView):
    queryset = Application.objects.select_related('job', 'applicant')
    serializer_class = ApplicationStatusUpdateSerializer
    permission_classes = [IsAuthenticated, IsRecruiterOfApplication]

    def perform_update(self, serializer):
        application = serializer.save()

        # Tạo thông báo cho ứng viên khi trạng thái thay đổi
        status_display = application.get_status_display()
        message = f"Hồ sơ của bạn cho công việc \"{application.job.title}\" đã được cập nhật trạng thái: {status_display}."
        Notification.objects.create(
            recipient=application.applicant,
            message=message
        )


#firebase
class FirebaseTokenAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        firebase_uid = f"user_{user.id}"  # Đảm bảo unique

        token = generate_firebase_custom_token(firebase_uid)
        return Response({'firebase_custom_token': token.decode('utf-8')})
