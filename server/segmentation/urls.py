from django.conf.urls import patterns, url
from segmentation.views import segmentation, task_segment, task_quality

urlpatterns = patterns(
    '',

    url(r'^segmentation$',
        segmentation, name='segmentation.segmentation'),

    url(r'^task$',
        task_segment, name='segmentation.task_segment'),

    url(r'^quality$',
        task_quality, name='segmentation.task_quality'),

    url(r'^task/(?P<dataset_id>\w+)$',
        task_segment),

    url(r'^quality/(?P<dataset_id>\w+)$',
        task_quality),
)
