from rest_framework import serializers
from .models import *


class BaseSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        d = super().to_representation(instance)
        # d['profile_picture'] = instance.profile_picture.url if instance.profile_picture else None
        return d


class UserRegisterSerializer(BaseSerializer):
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password', 'password2', 'role']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password": "Mật khẩu không khớp!"})
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)

        if user.role == User.EMPLOYER:
            user.is_verified = False
            user.save()

        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'username', 'email', 'role',
                  'is_verified', 'profile_picture', 'phone', 'address', 'date_joined']

    def to_representation(self, instance):
        data = super().to_representation(instance)

        data['profile_picture'] = instance.profile_picture.url if instance.profile_picture else ''

        return data

    def create(self, validated_data):
        data = validated_data.copy()
        u = User(**data)
        if 'password' in data:
            u.set_password(data['password'])
        u.save()
        return u


class JobSerializer(BaseSerializer):
    job_type_name = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = '__all__'
        read_only_fields = ['recruiter', 'company']

    def get_job_type_name(self, obj):
            return obj.job_type.name if obj.job_type else None

class JobSearchSerializer(BaseSerializer):
    company_name = serializers.SerializerMethodField()
    job_type = serializers.SerializerMethodField()
    total_views = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = [
            'id', 'title', 'location', 'salary', 'company_name', 'start_date',
            'job_type', 'total_views']
    def get_company_name(self, obj):
        return obj.company.name if obj.company else None

    def get_job_type(self, obj):
        return obj.job_type.name if obj.job_type else None

    def get_total_views(self, obj):
        return obj.views.count()

class JobStatsSerializer(serializers.ModelSerializer):
    total_views = serializers.SerializerMethodField()
    total_applications = serializers.SerializerMethodField()
    company_name = serializers.SerializerMethodField()


    class Meta:
        model = Job
        fields = [
            'id', 'created_date', 'updated_date', 'title', 'description', 'location', 'total_views',
            'salary', 'job_type', 'company_name', 'total_applications', 'start_date', 'end_date',
        ]

    def get_total_views(self, obj):
        return obj.views.count()

    def get_total_applications(self, obj):
        return obj.application_set.count()

    def get_company_name(self, obj):
        return obj.company.name if obj.company else None


class JobAnalyticsSerializer(serializers.ModelSerializer):

    total_applications = serializers.SerializerMethodField()
    suitable_candidates = serializers.SerializerMethodField()
    total_views = serializers.SerializerMethodField()
    scheduled_interviews = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = [
            'id', 'created_date', 'title',
            'total_applications', 'suitable_candidates', 'total_views', 'scheduled_interviews',
             'end_date'
        ]

    def get_job_type_name(self, obj):
        return obj.job_type.name if obj.job_type else None

    def get_company_name(self, obj):
        return obj.company.name if obj.company else None

    def get_total_applications(self, obj):
        return obj.application_set.count()

    def get_suitable_candidates(self, obj):
        return obj.application_set.filter(status='accepted').count()


    def get_total_views(self, obj):
        return obj.views.count()

    def get_scheduled_interviews(self, obj):
        return obj.application_set.filter(status='interview').count()


class JobStatSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    application_count = serializers.IntegerField()
    qualified_count = serializers.IntegerField()
    qualification_ratio = serializers.FloatField()


class JobTypeSerializer(BaseSerializer):
    class Meta:
        model = JobType
        fields = ['id', 'name']


class ApplicantDetailSerializer(serializers.ModelSerializer):
    applicant = UserSerializer()

    class Meta:
        model = Application
        fields = ['applicant', 'status']


class CVSerializer(serializers.ModelSerializer):
    file = serializers.FileField(required=False, allow_null=True, read_only=True)
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = CV
        fields = ['id', 'title', 'file', 'file_url', 'created_date', 'updated_date']
        read_only_fields = ['created_date', 'updated_date']

    def get_file_url(self, obj):
        if obj.file:
            return obj.file.url
        return None

    def create(self, validated_data):
        url = self.context['request'].data.get('url')

        if url:
            validated_data['file'] = url

        instance = super().create(validated_data)
        return instance

class ApplicationSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source='job.title', read_only=True)
    company_name = serializers.CharField(source='job.company.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Application
        fields = ['id', 'job', 'job_title', 'company_name', 'cv', 'status', 'status_display', 'created_date']
        read_only_fields = ['status', 'created_date']

class ApplicationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = ['job', 'cv', 'applicant']


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'


class FavoriteJobSerializer(serializers.ModelSerializer):
    job_detail = JobSerializer(source='job', read_only=True)

    class Meta:
        model = FavoriteJob
        fields = ['id', 'job', 'job_detail']


class CVDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = CV
        fields = [
            'id',
            'title',
            'file',
            'created_date',
            'updated_date'
        ]
        read_only_fields = ['id', 'created_date', 'updated_date']


class ApplicantSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name',
                  'phone', 'address', 'profile_picture']


class CVSerializer2(serializers.ModelSerializer):

    class Meta:
        model = CV
        fields = ['id', 'title', 'file', 'created_date', 'updated_date']


class ApplicationSerializer2(serializers.ModelSerializer):
    applicant = ApplicantSerializer(read_only=True)
    cv_details = CVSerializer2(source='cv', read_only=True)

    class Meta:
        model = Application
        fields = ['id', 'job', 'applicant', 'cv', 'cv_details', 'status',
                  'recruiter_notes', 'created_date', 'updated_date']
        read_only_fields = ['created_date', 'updated_date']


class ApplicationListSerializer2(serializers.ModelSerializer):

    class Meta:
        model = Application
        fields = ['id', 'job', 'applicant', 'cv', 'status',
                  'recruiter_notes', 'created_date', 'updated_date']
        read_only_fields = ['created_date', 'updated_date']


class InterviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interview
        fields = ['id', 'application', 'date', 'location', 'link', 'notes']


class AdminUserSerializer(serializers.ModelSerializer):
    stats = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role',
                  'is_active', 'is_verified', 'phone', 'address', 'profile_picture',
                  'date_joined', 'last_login', 'stats']

    def to_representation(self, instance):
        data = super().to_representation(instance)

        data['profile_picture'] = instance.profile_picture.url if instance.profile_picture else ''

        return data

    def get_stats(self, obj):
        if obj.role == 'job_seeker':
            return {
                'total_applications': Application.objects.filter(applicant=obj).count(),
                'total_jobs_posted': 0,
                'cv_count': CV.objects.filter(applicant=obj).count()
            }
        elif obj.role == 'employer':
            recruiter_profile = getattr(obj, 'recruiterprofile', None)
            if recruiter_profile:
                return {
                    'total_applications': 0,
                    'total_jobs_posted': Job.objects.filter(recruiter=recruiter_profile).count(),
                    'cv_count': 0
                }
        return {'total_applications': 0, 'total_jobs_posted': 0, 'cv_count': 0}


class AdminCompanySerializer(serializers.ModelSerializer):
    stats = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = ['id', 'name', 'description', 'website', 'location', 'logo',
                  'phone', 'email', 'active', 'created_date', 'stats']

    def get_stats(self, obj):
        return {
            'total_jobs': Job.objects.filter(company=obj).count(),
            'total_recruiters': RecruiterProfile.objects.filter(company=obj).count(),
            'total_applications': Application.objects.filter(job__company=obj).count()
        }


class AdminJobTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobType
        fields = ['id', 'name']


class AdminRecruiterSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = RecruiterProfile
        fields = ['id', 'user']

    def get_user(self, obj):
        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'email': obj.user.email
        }


class AdminJobSerializer(serializers.ModelSerializer):
    company = AdminCompanySerializer(read_only=True)
    recruiter = AdminRecruiterSerializer(read_only=True)
    job_type = AdminJobTypeSerializer(read_only=True)
    stats = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = ['id', 'title', 'description', 'location', 'salary', 'active',
                  'created_date', 'updated_date', 'start_date', 'end_date',
                  'company', 'recruiter', 'job_type', 'stats']

    def get_stats(self, obj):
        return {
            'total_applications': Application.objects.filter(job=obj).count(),
            'total_views': JobView.objects.filter(job=obj).count()
        }


class AdminCVSerializer(serializers.ModelSerializer):
    class Meta:
        model = CV
        fields = ['id', 'title', 'file']


class AdminApplicantSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class AdminApplicationSerializer(serializers.ModelSerializer):
    job = serializers.SerializerMethodField()
    applicant = AdminApplicantSerializer(read_only=True)
    cv = AdminCVSerializer(read_only=True)

    class Meta:
        model = Application
        fields = ['id', 'status', 'recruiter_notes', 'created_date',
                  'job', 'applicant', 'cv']

    def get_job(self, obj):
        return {
            'id': obj.job.id,
            'title': obj.job.title,
            'company': {
                'name': obj.job.company.name
            }
        }


class AdminVerificationUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'phone']


class AdminVerificationSerializer(serializers.ModelSerializer):
    user = AdminVerificationUserSerializer(read_only=True)
    documents = serializers.SerializerMethodField()

    class Meta:
        model = VerificationRequest
        fields = ['id', 'user', 'status', 'note', 'created_date', 'updated_date', 'documents']

    def get_documents(self, obj):
        return [
            {
                'type': 'business_license',
                'url': 'https://cloudinary.com/doc/license.pdf'
            }
        ]