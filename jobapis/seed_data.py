from django.contrib.auth import get_user_model
from django.utils import timezone
from jobs.models import Company, RecruiterProfile, JobType, Job, Skill, CV, Application, Notification, Message, Interview, DeviceToken
from decimal import Decimal

# Lấy model User
User = get_user_model()

# Xóa dữ liệu cũ (tùy chọn, để làm sạch database trước khi insert)
User.objects.all().delete()
Company.objects.all().delete()
RecruiterProfile.objects.all().delete()
JobType.objects.all().delete()
Job.objects.all().delete()
Skill.objects.all().delete()
CV.objects.all().delete()
Application.objects.all().delete()
Notification.objects.all().delete()
Message.objects.all().delete()
Interview.objects.all().delete()
DeviceToken.objects.all().delete()

# # 1. Tạo người dùng (jobs_user, jobs_user_groups, jobs_user_user_permissions)
# admin_user = User.objects.create_superuser(
#     username='admin',
#     email='admin@example.com',
#     password='123',
#     role=User.ADMIN,
#     is_verified=True,
#     phone='0123456789',
#     address='Hanoi, Vietnam',
#     profile_picture='profile_pictures/admin.jpg'  # Giả lập Cloudinary
# )

job_seeker1 = User.objects.create_user(
    username='jobseeker1',
    email='jobseeker1@example.com',
    password='jobseeker123',
    role=User.JOB_SEEKER,
    is_verified=True,
    phone='0987654321',
    address='HCMC, Vietnam',
    profile_picture='profile_pictures/jobseeker1.jpg'
)

job_seeker2 = User.objects.create_user(
    username='jobseeker2',
    email='jobseeker2@example.com',
    password='jobseeker123',
    role=User.JOB_SEEKER,
    is_verified=True,
    phone='0987654322',
    address='Danang, Vietnam',
    profile_picture='profile_pictures/jobseeker2.jpg'
)

employer = User.objects.create_user(
    username='employer',
    email='employer@example.com',
    password='employer123',
    role=User.EMPLOYER,
    is_verified=True,
    phone='0912345678',
    address='Hanoi, Vietnam',
    profile_picture='profile_pictures/employer.jpg'
)

# 2. Tạo công ty (jobs_company)
company1 = Company.objects.create(
    name='TechCorp',
    description='A leading tech company',
    website='https://techcorp.com',
    location='Hanoi, Vietnam',
    logo='logos/techcorp_logo.jpg'  # Giả lập Cloudinary
)

company2 = Company.objects.create(
    name='InnovateSoft',
    description='Software solutions provider',
    website='https://innovatesoft.com',
    location='HCMC, Vietnam',
    logo='logos/innovatesoft_logo.jpg'
)

# 3. Tạo hồ sơ nhà tuyển dụng (jobs_recruiterprofile)
recruiter_profile = RecruiterProfile.objects.create(
    user=employer,
    company=company1
)

# 4. Tạo loại công việc (jobs_jobtype)
job_type1 = JobType.objects.create(name='Full-time')
job_type2 = JobType.objects.create(name='Part-time')

# 5. Tạo công việc (jobs_job)
job1 = Job.objects.create(
    recruiter=recruiter_profile,
    job_type=job_type1,
    title='Senior Python Developer',
    description='Develop and maintain web applications using Python and Django',
    location='Hanoi, Vietnam',
    salary=Decimal('30000000'),
    company=company1
)

job2 = Job.objects.create(
    recruiter=recruiter_profile,
    job_type=job_type2,
    title='Frontend Developer',
    description='Build responsive web interfaces with React',
    location='HCMC, Vietnam',
    salary=Decimal('20000000'),
    company=company2
)

# 6. Tạo kỹ năng (jobs_skill)
skill_python = Skill.objects.create(name='Python')
skill_django = Skill.objects.create(name='Django')
skill_react = Skill.objects.create(name='React')
skill_sql = Skill.objects.create(name='SQL')

# 7. Tạo CV (jobs_cv, jobs_cv_skills)
cv1 = CV.objects.create(
    applicant=job_seeker1,
    title='Software Engineer CV',
    file='cv/jobseeker1_cv.pdf'  # Giả lập đường dẫn file
)
cv1.skills.add(skill_python, skill_django, skill_sql)

cv2 = CV.objects.create(
    applicant=job_seeker2,
    title='Frontend Developer CV',
    file='cv/jobseeker2_cv.pdf'
)
cv2.skills.add(skill_react)

# 8. Tạo ứng tuyển (jobs_application)
application1 = Application.objects.create(
    job=job1,
    applicant=job_seeker1,
    cv=cv1,
    status='pending'
)

application2 = Application.objects.create(
    job=job2,
    applicant=job_seeker2,
    cv=cv2,
    status='reviewed'
)

# 9. Tạo thông báo (jobs_notification)
notification1 = Notification.objects.create(
    recipient=job_seeker1,
    message='Your application for Senior Python Developer has been received.'
)

notification2 = Notification.objects.create(
    recipient=job_seeker2,
    message='Your application for Frontend Developer has been reviewed.'
)

# 10. Tạo tin nhắn (jobs_message)
message1 = Message.objects.create(
    sender=employer,
    receiver=job_seeker1,
    content='We would like to schedule an interview for the Senior Python Developer position.'
)

message2 = Message.objects.create(
    sender=employer,
    receiver=job_seeker2,
    content='Your application for Frontend Developer has been reviewed. Please check your email.'
)

# 11. Tạo lịch phỏng vấn (jobs_interview)
interview1 = Interview.objects.create(
    application=application1,
    date=timezone.now() + timezone.timedelta(days=3),
    location='TechCorp HQ, Hanoi',
    link='https://zoom.us/j/123456789',
    notes='Bring your portfolio'
)

interview2 = Interview.objects.create(
    application=application2,
    date=timezone.now() + timezone.timedelta(days=5),
    location='InnovateSoft Office, HCMC',
    link='https://zoom.us/j/987654321',
    notes='Prepare a React demo'
)

# 12. Tạo DeviceToken với FCM token giả (jobs_devicetoken)
device_token1 = DeviceToken.objects.create(
    user=job_seeker1,
    token='fcm_token_test_1234567890abcdefghijklmnopqrstuvwxyz',
    device_id='device-123',
    device_type='android',
    active=True
)

device_token2 = DeviceToken.objects.create(
    user=job_seeker2,
    token='fcm_token_test_0987654321zyxwvutsrqponmlkjihgfedcba',
    device_id='device-456',
    device_type='ios',
    active=True
)

# In thông tin để kiểm tra
print("Inserted data successfully!")
print(f"Users: {User.objects.count()}")
print(f"Companies: {Company.objects.count()}")
print(f"Jobs: {Job.objects.count()}")
print(f"Applications: {Application.objects.count()}")
print(f"DeviceTokens: {DeviceToken.objects.count()}")