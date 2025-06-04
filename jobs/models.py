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
    profile_picture = CloudinaryField(blank=True, null=True, default='https://res.cloudinary.com/dt3k9eyfz/image/upload/v1748975047/qvrmont4ahizqkxvum6m.png')

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
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

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

    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.title} - {self.company.name}"


class JobView(BaseModel):

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='views')
    viewer = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)  # null cho anonymous user
    ip_address = models.GenericIPAddressField(null=True, blank=True)  # Để track anonymous views

    class Meta:
        unique_together = ('job', 'viewer', 'ip_address')

    def __str__(self):
        viewer_name = self.viewer.username if self.viewer else f"Anonymous ({self.ip_address})"
        return f"{viewer_name} viewed {self.job.title}"



class CV(BaseModel):
    applicant = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='cv/')

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


class Interview(BaseModel):
    application = models.OneToOneField(Application, on_delete=models.CASCADE)
    date = models.DateTimeField(db_index=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    link = models.URLField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Interview for {self.application.applicant.username} - {self.application.job.title}"


class CVView(BaseModel):
    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name='views')
    viewer = models.ForeignKey(RecruiterProfile, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('cv', 'viewer')

    def __str__(self):
        return f"{self.viewer.user.username} viewed {self.cv.title}"


class CVSaveAction(BaseModel):
    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name='saves')
    recruiter = models.ForeignKey(RecruiterProfile, on_delete=models.CASCADE)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('cv', 'recruiter')

    def __str__(self):
        return f"{self.recruiter.user.username} saved {self.cv.title}"


class VerificationRequest(BaseModel):
    STATUS_CHOICES = [
        ('pending', 'Đang chờ duyệt'),
        ('approved', 'Đã duyệt'),
        ('rejected', 'Bị từ chối'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    note = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.status}"


class FavoriteJob(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="favorite_jobs")
    job = models.ForeignKey(Job, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'job')

    def __str__(self):
        return f"{self.user.username} - {self.job.title}"

