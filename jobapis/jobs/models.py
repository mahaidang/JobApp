from django.db import models
from django.contrib.auth.models import AbstractUser
from ckeditor.fields import RichTextField
from cloudinary.models import CloudinaryField


class User(AbstractUser):
    JOB_SEEKER = 'job_seeker'
    EMPLOYER = 'employer'
    ADMIN = 'admin'

    ROLE_CHOICES = [
        (JOB_SEEKER, 'Người tìm việc'),
        (EMPLOYER, 'Nhà tuyển dụng'),
        (ADMIN, 'Quản trị viên'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=JOB_SEEKER)
    is_verified = models.BooleanField(default=False)
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    profile_picture = CloudinaryField('profile_pictures/', blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = self.ADMIN
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class BaseModel(models.Model):
    active = models.BooleanField(default=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ['-id']


class Company(BaseModel):
    name = models.CharField(max_length=255)
    description = models.TextField()
    website = models.URLField(blank=True, null=True)
    location = models.CharField(max_length=255)
    logo = CloudinaryField(null=True, blank=True)

    def __str__(self):
        return self.name


class RecruiterProfile(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.username} - {self.company.name}"


class JobType(BaseModel):
    name = models.CharField(max_length=50, unique=True)


class Job(BaseModel):
    recruiter = models.ForeignKey(RecruiterProfile, on_delete=models.CASCADE)
    job_type = models.ForeignKey(JobType, on_delete=models.SET_NULL, null=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    location = models.CharField(max_length=255)
    salary = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="jobs")

    def __str__(self):
        return f"{self.title} - {self.company.name}"



class Skill(BaseModel):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class CV(BaseModel):
    applicant = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='cv/')
    skills = models.ManyToManyField(Skill, blank=True)

    def __str__(self):
        return f"{self.applicant.username} - {self.title}"


class Application(BaseModel):
    STATUS_CHOICES = [
        ('pending', 'Đang chờ'),
        ('reviewed', 'Đã xem'),
        ('interview', 'Phỏng vấn'),
        ('accepted', 'Được nhận'),
        ('rejected', 'Bị từ chối'),
    ]
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    applicant = models.ForeignKey(User, on_delete=models.CASCADE)
    cv = models.ForeignKey(CV, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    recruiter_notes = models.TextField(blank=True, null=True)  # Thêm trường ghi chú

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['job', 'applicant'],
                name='unique_job_applicant'
            )
        ]

    def __str__(self):
        return f"{self.applicant.username} - {self.job.title} ({self.status})"


class Notification(BaseModel):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    message = models.TextField()
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"To {self.recipient.username}: {self.message[:30]}..."


class Message(BaseModel):
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_messages")
    content = models.TextField()

    def __str__(self):
        return f"From {self.sender.username} to {self.receiver.username}"


class Interview(BaseModel):
    application = models.OneToOneField(Application, on_delete=models.CASCADE)
    date = models.DateTimeField(db_index=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    link = models.URLField(blank=True, null=True)  # Dùng cho phỏng vấn online
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Interview for {self.application.applicant.username} - {self.application.job.title}"


class DeviceToken(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='device_tokens')
    token = models.CharField(max_length=255, unique=True)
    device_id = models.CharField(max_length=255, blank=True, null=True)
    device_type = models.CharField(max_length=20, choices=[('android', 'Android'), ('ios', 'iOS'), ('web', 'Web')], default='web')
    active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('user', 'token')

    def __str__(self):
        return f"{self.user.username} - {self.token[:20]}..."


class CVView(BaseModel):
    """
    Model để theo dõi lượt xem hồ sơ CV từ nhà tuyển dụng thông qua ứng tuyển
    """
    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name='views')
    viewer = models.ForeignKey(RecruiterProfile, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('cv', 'viewer')

    def __str__(self):
        return f"{self.viewer.user.username} viewed {self.cv.title}"


class CVSaveAction(BaseModel):
    """
    Model để nhà tuyển dụng lưu lại CV (liên quan đến việc đã xem CV)
    """
    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name='saves')
    recruiter = models.ForeignKey(RecruiterProfile, on_delete=models.CASCADE)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('cv', 'recruiter')

    def __str__(self):
        return f"{self.recruiter.user.username} saved {self.cv.title}"
