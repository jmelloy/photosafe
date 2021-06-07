from django.contrib import admin
from .models import Photo
# Register your models here.

@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    pass
