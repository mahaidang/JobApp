from oauth2_provider.models import Application
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.generics import UpdateAPIView
from .firebase_service import generate_firebase_custom_token

from rest_framework import viewsets, generics, parsers, permissions, status
from django.contrib.auth import get_user_model, authenticate
from .serializers import UserRegisterSerializer, UserSerializer, EmployerVerificationSerializer, CVSerializer, \
    ApplicationSerializer, ApplicationStatusUpdateSerializer
from .models import CV, Application, Job,  Notification
from .perms import IsOwnerOrReadOnly


User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """Quản lý thông tin người dùng"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def me(self, request):
        """API lấy thông tin người dùng hiện tại"""
        return Response({
            "id": request.user.id,
            "username": request.user.username,
            "email": request.user.email
        })


class AuthViewSet(viewsets.ViewSet):
    """Xác thực người dùng"""
    permission_classes = [permissions.AllowAny]

    @action(detail=False, methods=['post'])
    def register(self, request):
        """API Đăng ký tài khoản"""
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
