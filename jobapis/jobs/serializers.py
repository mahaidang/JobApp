from django.contrib.auth import authenticate
from oauth2_provider.models import Application
from rest_framework import serializers
from .models import User, Job, CV, Skill, Application

class BaseSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        d = super().to_representation(instance)
        # d['profile_picture'] = instance.profile_picture.url if instance.profile_picture else None
        return d


class UserRegisterSerializer(BaseSerializer):
    password2 = serializers.CharField(write_only=True)  # Xác nhận mật khẩu

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 'role']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate(self, data):
        """Kiểm tra mật khẩu có khớp nhau không"""
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password": "Mật khẩu không khớp!"})
        return data

    def create(self, validated_data):
        """Tạo tài khoản và xử lý xác thực cho Employer"""
        validated_data.pop('password2')  # Loại bỏ password2
        user = User.objects.create_user(**validated_data)

        # Nhà tuyển dụng cần admin xác thực
        if user.role == User.EMPLOYER:
            user.is_verified = False  # Chưa được xác thực
            user.save()

        return user


class UserSerializer(BaseSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'is_verified']


class EmployerVerificationSerializer(BaseSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "is_verified"]
        read_only_fields = ["id", "username"]





class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ['id', 'name']

class CVSerializer(serializers.ModelSerializer):
    skills = SkillSerializer(many=True, read_only=True)
    skill_ids = serializers.PrimaryKeyRelatedField(
        queryset=Skill.objects.all(), many=True, write_only=True, source='skills'
    )
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = CV
        fields = ['id', 'title', 'file', 'file_url', 'skills', 'skill_ids', 'created_date', 'updated_date']
        read_only_fields = ['created_date', 'updated_date']

    def get_file_url(self, obj):
        if obj.file:
            return obj.file.url
        return None


class ApplicationSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source='job.title', read_only=True)
    company_name = serializers.CharField(source='job.company.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Application
        fields = ['id', 'job', 'job_title', 'company_name', 'cv', 'status', 'status_display', 'created_date']
        read_only_fields = ['status', 'created_date']


class ApplicationStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = ['status']
