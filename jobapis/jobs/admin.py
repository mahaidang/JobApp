from allauth.socialaccount.models import SocialApp, SocialAccount, SocialToken
from django.contrib import admin
from django.contrib.sites.models import Site
from django.db.models import Count
from django.template.response import TemplateResponse
from django.utils.html import mark_safe
from django import forms
from ckeditor_uploader.widgets import CKEditorUploadingWidget
from django.urls import path
from .models import User


class MyAdminSite(admin.AdminSite):
    site_header = 'OU eJob'

    def get_urls(self):
        return [
            path('job-stats/', self.stats_view)
        ] + super().get_urls()

    def stats_view(self, request):
        stats = Job.objects.annotate(lesson_count=Count('lesson__id')).values('id', 'subject', 'lesson_count')

        return TemplateResponse(request,'admin/stats_view.html', {
            'stats': stats
        })

admin_site = MyAdminSite(name='admin')

# admin_site = site
admin_site.register(User)

# Đăng ký các mô hình của django-allauth
admin_site.register(SocialApp)  # Đăng ký SocialApp model
admin_site.register(SocialAccount)  # Đăng ký SocialAccount model
admin_site.register(SocialToken)  # Đăng ký SocialToken model

admin_site.register(Site)