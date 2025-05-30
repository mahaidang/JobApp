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
    profile_picture = CloudinaryField(folder='profile_pictures', blank=True, null=True)

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


class JobType(models.Model):
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


    def __str__(self):
        return self.name

class Skill(BaseModel):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


from cloudinary.models import CloudinaryField

class CV(BaseModel):
    applicant = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    file = CloudinaryField(resource_type='raw', folder='cv')
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