# filters.py
import django_filters
from .models import Job
from rest_framework import filters


class JobFilter(django_filters.FilterSet):
    min_salary = django_filters.NumberFilter(field_name="salary", lookup_expr='gte')
    max_salary = django_filters.NumberFilter(field_name="salary", lookup_expr='lte')
    keyword = django_filters.CharFilter(method='filter_by_keyword')
    location = django_filters.CharFilter(lookup_expr='icontains')
    job_type = django_filters.CharFilter(field_name='job_type__name', lookup_expr='icontains')

    class Meta:
        model = Job
        fields = []

    def filter_by_keyword(self, queryset, name, value):
        return queryset.filter(
            title__icontains=value
        )
