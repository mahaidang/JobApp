from django.contrib.auth import get_user_model
from django.utils import timezone
from jobs.models import Company, RecruiterProfile, JobType, Job, CV, Application, Interview
from decimal import Decimal

User = get_user_model()

User.objects.all().delete()
Company.objects.all().delete()
RecruiterProfile.objects.all().delete()
JobType.objects.all().delete()
Job.objects.all().delete()
CV.objects.all().delete()
Application.objects.all().delete()
Interview.objects.all().delete()

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

company1 = Company.objects.create(
    name='TechCorp',
    description='A leading tech company',
    website='https://techcorp.com',
    location='Hanoi, Vietnam',
    logo='logos/techcorp_logo.jpg'
)

company2 = Company.objects.create(
    name='InnovateSoft',
    description='Software solutions provider',
    website='https://innovatesoft.com',
    location='HCMC, Vietnam',
    logo='logos/innovatesoft_logo.jpg'
)

company3 = Company.objects.create(
    name='GreenTech',
    description='Green technology solutions',
    website='https://greentech.com',
    location='Hue, Vietnam',
    logo='logos/greentech_logo.jpg'
)

company4 = Company.objects.create(
    name='EduSmart',
    description='Education & eLearning platform',
    website='https://edusmart.com',
    location='Can Tho, Vietnam',
    logo='logos/edusmart_logo.jpg'
)

company5 = Company.objects.create(
    name='MediPlus',
    description='Healthcare software company',
    website='https://mediplus.com',
    location='Haiphong, Vietnam',
    logo='logos/mediplus_logo.jpg'
)

recruiter_profile = RecruiterProfile.objects.create(
    user=employer,
    company=company1
)

job_type1 = JobType.objects.create(name='Full-time')
job_type2 = JobType.objects.create(name='Part-time')
job_type3 = JobType.objects.create(name='Internship')
job_type4 = JobType.objects.create(name='Remote')
job_type5 = JobType.objects.create(name='Contract')

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

job_list = [
    ("Backend Developer", "Node.js and MongoDB experience", "Hue, Vietnam", Decimal('18000000'), company3, job_type1),
    ("UI/UX Designer", "Design intuitive interfaces", "Hanoi, Vietnam", Decimal('22000000'), company1, job_type1),
    ("Mobile App Developer", "Flutter & Dart expertise", "HCMC, Vietnam", Decimal('25000000'), company2, job_type2),
    ("QA Engineer", "Manual and automated testing", "Danang, Vietnam", Decimal('17000000'), company4, job_type3),
    ("Project Manager", "Agile experience required", "Hanoi, Vietnam", Decimal('35000000'), company1, job_type1),
    ("Business Analyst", "Work with stakeholders", "HCMC, Vietnam", Decimal('24000000'), company2, job_type4),
    ("DevOps Engineer", "CI/CD pipeline development", "Can Tho, Vietnam", Decimal('26000000'), company4, job_type4),
    ("Data Scientist", "Python, ML, data modeling", "Hanoi, Vietnam", Decimal('38000000'), company1, job_type1),
    ("HR Officer", "Recruitment and training", "Hue, Vietnam", Decimal('15000000'), company3, job_type2),
    ("Digital Marketer", "SEO/SEM campaigns", "HCMC, Vietnam", Decimal('20000000'), company2, job_type1),
    ("AI Engineer", "AI & NLP applications", "Hanoi, Vietnam", Decimal('42000000'), company1, job_type5),
    ("IT Support", "End-user support", "Haiphong, Vietnam", Decimal('14000000'), company5, job_type2),
    ("Content Writer", "Blog, copywriting", "Can Tho, Vietnam", Decimal('13000000'), company4, job_type3),
    ("System Admin", "Server and network maintenance", "Danang, Vietnam", Decimal('23000000'), company4, job_type1),
    ("Cloud Engineer", "AWS or Azure experience", "Hanoi, Vietnam", Decimal('36000000'), company1, job_type1),
    ("Security Analyst", "IT security protocols", "HCMC, Vietnam", Decimal('30000000'), company2, job_type1),
    ("Video Editor", "Adobe Premiere, After Effects", "Hanoi, Vietnam", Decimal('19000000'), company1, job_type5),
    ("Customer Support", "Handle client inquiries", "Danang, Vietnam", Decimal('16000000'), company4, job_type2),
    ("Tech Lead", "Lead a development team", "Hanoi, Vietnam", Decimal('45000000'), company1, job_type1),
    ("Product Owner", "Manage product lifecycle", "HCMC, Vietnam", Decimal('40000000'), company2, job_type1),
]

for title, description, location, salary, company, job_type in job_list:
    Job.objects.create(
        recruiter=recruiter_profile,
        job_type=job_type,
        title=title,
        description=description,
        location=location,
        salary=salary,
        company=company
    )

cv1 = CV.objects.create(
    applicant=job_seeker1,
    title='Software Engineer CV',
    file='cv/jobseeker1_cv.pdf'
)

cv2 = CV.objects.create(
    applicant=job_seeker2,
    title='Frontend Developer CV',
    file='cv/jobseeker2_cv.pdf'
)

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



print("Inserted data successfully!")
print(f"Users: {User.objects.count()}")
print(f"Companies: {Company.objects.count()}")
print(f"Jobs: {Job.objects.count()}")
print(f"Applications: {Application.objects.count()}")
