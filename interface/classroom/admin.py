from django.contrib import admin
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import *


class FSUserInline(admin.StackedInline):
    model = FSUser
    can_delete = False
    verbose_name_plural = 'Classroom Users'


class FSUserAdmin(BaseUserAdmin):
    inlines = (FSUserInline,)


admin.site.unregister(User)
admin.site.register(User, FSUserAdmin)
admin.site.register(Classroom)
admin.site.register(DockerInstances)
admin.site.register(Assignment)