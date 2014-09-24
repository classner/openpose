from django.contrib import admin

from common.admin import AutoUserMixin

from pose.models import ParsePose

admin.site.register(ParsePose)
