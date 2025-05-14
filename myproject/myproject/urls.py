from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('main.urls')),
    path('api/job/', include('institutions.urls')),
    path('auth/', include('social_django.urls', namespace='social'))
]
