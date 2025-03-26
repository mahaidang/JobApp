from oauth2_provider.models import Application
from rest_framework.decorators import action
from rest_framework.response import Response

from rest_framework import viewsets, generics, parsers, permissions, status
from django.contrib.auth import get_user_model, authenticate

from .serializers import UserRegisterSerializer, UserSerializer, EmployerVerificationSerializer

from rest_framework import viewsets

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