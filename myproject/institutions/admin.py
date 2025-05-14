from django.contrib import admin

from institutions.models import Institution, InstitutionMember, Job,JobApplication


admin.site.register(Institution)
admin.site.register(InstitutionMember)
admin.site.register(Job)
admin.site.register(JobApplication)


