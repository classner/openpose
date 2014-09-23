from django.contrib import admin

from imagekit.admin import AdminThumbnail
from common.admin import AutoUserMixin

from photos.models import FlickrUser, PhotoDataset, Photo

admin.site.register(FlickrUser)
admin.site.register(PhotoDataset)

class PhotoAdmin(AutoUserMixin, admin.ModelAdmin):
    fieldsets = [
        (None, {
            'fields': ['added', 'user', 'image_orig', 'admin_thumb_span6', 'aspect_ratio', 'dataset',
                       'description', 'exif',
                       'flickr_user', 'flickr_id']
        }),
    ]

    # fields
    readonly_fields = ['added', 'admin_thumb_span6']
    list_display = ['user', 'admin_thumb_span1', 'dataset',
                    'added']

    # field display
    list_filter = ['added']
    search_fields = ['user', 'description']
    date_hierarchy = 'added'

    admin_thumb_span6 = AdminThumbnail(image_field='image_200')
    admin_thumb_span1 = AdminThumbnail(image_field='image_200')

    inlines = []

admin.site.register(Photo, PhotoAdmin)
