from django.conf.urls import patterns, url
from segmentation.views import segmentation, task

urlpatterns = patterns(
    '',

    url(r'^segmentation$',
        segmentation, name='segmentation'),

    url(r'^$',
        task, name='task'),
)
