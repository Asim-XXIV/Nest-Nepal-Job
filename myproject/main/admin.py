from django.contrib import admin

from main.models import UserProfile, CustomUser  # Absolute import from the same directory


admin.site.register(UserProfile)
admin.site.register(CustomUser)


