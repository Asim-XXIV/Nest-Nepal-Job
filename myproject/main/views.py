from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import update_session_auth_hash
from .models import CustomUser, UserProfile
from .serializers import RegisterSerializer, LoginSerializer, UserProfileSerializer
from django.utils import timezone
from datetime import timedelta
from .permissions import IsAdminUserRole
from django.shortcuts import get_object_or_404


class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            UserProfile.objects.create(user=user)  # create empty profile
            return Response({'message': 'User registered successfully'}, status=201)
        return Response(serializer.errors, status=400)


class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            response = Response({
                "message": "Login successful",
                "role": user.role,
                "user_id": user.id,
                "username": user.username,
            })

            access_expiry = timezone.now() + timedelta(days=1)
            refresh_expiry = timezone.now() + timedelta(days=7)

            response.set_cookie(
                key='access_token',
                value=access_token,
                expires=access_expiry,
                httponly=True,
                secure=False,
                samesite='Lax'
            )
            response.set_cookie(
                key='refresh_token',
                value=refresh_token,
                expires=refresh_expiry,
                httponly=True,
                secure=False,
                samesite='Lax'
            )
            response.set_cookie('role', user.role)
            response.set_cookie('user_id', user.id)
            response.set_cookie('username', user.username)

            return response
        return Response(serializer.errors, status=400)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        response = Response({"message": "Logout successful"}, status=205)

        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        response.delete_cookie('role')

        return response


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")
        confirm_password = request.data.get("confirm_password")

        if not user.check_password(old_password):
            return Response({"error": "Old password is incorrect"}, status=400)
        if new_password != confirm_password:
            return Response({"error": "Passwords do not match"}, status=400)

        user.set_password(new_password)
        user.save()
        update_session_auth_hash(request, user)

        return Response({"message": "Password changed successfully"}, status=200)


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            profile = request.user.userprofile
            serializer = UserProfileSerializer(profile)
            return Response(serializer.data)
        except UserProfile.DoesNotExist:
            return Response({'error': 'Profile not found'}, status=404)

    def put(self, request):
        try:
            profile = request.user.userprofile
            serializer = UserProfileSerializer(profile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=400)
        except UserProfile.DoesNotExist:
            return Response({'error': 'Profile not found'}, status=404)


class AdminUserListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserRole]

    def get(self, request):
        users = CustomUser.objects.all()
        data = [
            {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "role": user.role,
                "is_active": user.is_active,
                "created_at": user.created_at,
            }
            for user in users
        ]
        return Response(data)


class AdminUserDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserRole]

    def get(self, request, user_id):
        user = get_object_or_404(CustomUser, id=user_id)
        profile = getattr(user, 'userprofile', None)
        profile_data = UserProfileSerializer(profile).data if profile else None

        return Response({
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at,
            "profile": profile_data,
        })

    def put(self, request, user_id):
        user = get_object_or_404(CustomUser, id=user_id)
        profile = getattr(user, 'userprofile', None)

        user.username = request.data.get('username', user.username)
        user.email = request.data.get('email', user.email)
        user.role = request.data.get('role', user.role)
        user.is_active = request.data.get('is_active', user.is_active)
        user.save()

        if profile:
            serializer = UserProfileSerializer(profile, data=request.data.get('profile', {}), partial=True)
            if serializer.is_valid():
                serializer.save()

        return Response({"message": "User updated successfully"})

    def delete(self, request, user_id):
        user = get_object_or_404(CustomUser, id=user_id)
        user.delete()
        return Response({"message": "User deleted"}, status=204)


class RefreshTokenView(APIView):
    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')
        if refresh_token is None:
            return Response({"error": "Refresh token missing"}, status=401)

        try:
            token = RefreshToken(refresh_token)
            access_token = str(token.access_token)

            response = Response({'access': access_token})

            response.set_cookie(
                key='access_token',
                value=access_token,
                httponly=True,
                samesite='Lax',
                secure=False
            )

            return response
        except TokenError:
            return Response({"error": "Invalid refresh token"}, status=400)
