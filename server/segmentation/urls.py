from django.conf.urls import patterns, url
from segmentation.views import segmentation, task

urlpatterns = patterns(
    '',

    url(r'^task/segmentation$',
        segmentation, name='segmentation.segmentation'),

    url(r'^task$',
        task, name='task'),
)
