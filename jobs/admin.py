from allauth.socialaccount.models import SocialApp, SocialAccount, SocialToken
from django.contrib import admin
from django.contrib.sites.models import Site
from .models import *
from django.contrib.admin import AdminSite

class MyAdminSite(AdminSite):
    site_header = 'OU eJob'

admin_site = MyAdminSite(name='admin')
# Hàm đăng ký nhanh tất cả các field trong admin
def auto_register(model):
    class AutoAdmin(admin.ModelAdmin):
        list_display = [f.name for f in model._meta.fields]
    admin_site.register(model, AutoAdmin)

# Đăng ký các model với hiển thị đầy đủ cột
auto_register(User)
auto_register(SocialApp)
auto_register(SocialAccount)
auto_register(SocialToken)
auto_register(Site)
auto_register(Company)
auto_register(Interview)
auto_register(Application)
auto_register(CV)
auto_register(Job)
auto_register(JobView)
