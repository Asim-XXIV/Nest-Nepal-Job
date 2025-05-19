
from rest_framework import serializers
from .models import Institution, InstitutionMember, Job, JobApplication
from main.models import CustomUser
from main.serializers import UserProfileSerializer

class InstitutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Institution
        fields = ['id', 'name', 'description', 'location', 'created_at']
        read_only_fields = ['created_at']

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Institution name cannot be empty.")
        return value

class InstitutionMemberSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    institution = InstitutionSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(), source='user', write_only=True
    )
    institution_id = serializers.PrimaryKeyRelatedField(
        queryset=Institution.objects.all(), source='institution', write_only=True
    )

    class Meta:
        model = InstitutionMember
        fields = ['id', 'user', 'user_id', 'institution', 'institution_id', 'role', 'joined_at']
        read_only_fields = ['joined_at']

    def validate(self, data):
        if InstitutionMember.objects.filter(
            user=data['user'], institution=data['institution']
        ).exists():
            raise serializers.ValidationError("This user is already a member of this institution.")
        return data

class JobSerializer(serializers.ModelSerializer):
    institution = InstitutionSerializer(read_only=True)
    posted_by = UserProfileSerializer(read_only=True)
    institution_id = serializers.PrimaryKeyRelatedField(
        queryset=Institution.objects.all(), source='institution', write_only=True, required=False
    )

    class Meta:
        model = Job
        fields = ['id', 'title', 'description', 'location', 'salary_range', 'job_type', 'status',
                  'institution', 'institution_id', 'posted_by', 'created_at']
        read_only_fields = ['created_at', 'posted_by']

    def validate(self, data):
        if 'institution' in data and not InstitutionMember.objects.filter(
            user=self.context['request'].user, institution=data['institution'], role='company'
        ).exists():
            raise serializers.ValidationError("You must be a company member of the institution to post a job.")
        return data

class JobApplicationSerializer(serializers.ModelSerializer):
    job = JobSerializer(read_only=True)
    user = UserProfileSerializer(read_only=True)
    job_id = serializers.PrimaryKeyRelatedField(
        queryset=Job.objects.all(), source='job', write_only=True
    )

    class Meta:
        model = JobApplication
        fields = ['id', 'job', 'job_id', 'user', 'cover_letter', 'status', 'applied_at']
        read_only_fields = ['user', 'applied_at']

    def validate(self, data):
        if JobApplication.objects.filter(
            job=data['job'], user=self.context['request'].user
        ).exists():
            raise serializers.ValidationError("You have already applied for this job.")
        return data