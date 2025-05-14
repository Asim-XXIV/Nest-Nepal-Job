from rest_framework import serializers
from .models import Institution, InstitutionMember, Job, JobApplication
from django.contrib.auth import get_user_model

User = get_user_model()

class InstitutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Institution
        fields = ['name', 'description', 'location']

class InstitutionMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstitutionMember
        fields = ['user', 'institution', 'role']

class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = ['title', 'description', 'location', 'salary_range', 'job_type', 'status', 'institution', 'posted_by']

class JobApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobApplication
        fields = ['job', 'user', 'cover_letter', 'status']
