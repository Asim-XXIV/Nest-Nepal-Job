from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Institution, InstitutionMember, Job, JobApplication
from .serializers import InstitutionSerializer, InstitutionMemberSerializer, JobSerializer, JobApplicationSerializer
from main.permissions import IsAdmin, IsEmployer, IsJobSeeker, IsRecruiterOrAdmin


# Institutions View
class InstitutionListCreate(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]  # Only admins can manage institutions

    def get(self, request):
        institutions = Institution.objects.all()
        serializer = InstitutionSerializer(institutions, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = InstitutionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Institution Members View
class InstitutionMemberListCreate(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]  # Admins can manage members

    def get(self, request):
        members = InstitutionMember.objects.all()
        serializer = InstitutionMemberSerializer(members, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = InstitutionMemberSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Jobs View (For Employers to post)
class JobListCreate(APIView):
    permission_classes = [IsAuthenticated, IsEmployer]  # Employers can post jobs

    def get(self, request):
        jobs = Job.objects.all()
        serializer = JobSerializer(jobs, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = JobSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(posted_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Job Applications View (For Job Seekers to Apply and Admins/Employers to Review)
class JobApplicationListCreate(APIView):
    permission_classes = [IsAuthenticated, IsJobSeeker]  # Job Seekers can apply

    def get(self, request):
        applications = JobApplication.objects.all()
        serializer = JobApplicationSerializer(applications, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = JobApplicationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

