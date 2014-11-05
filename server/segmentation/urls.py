from django.conf.urls import patterns, url
from segmentation.views import segmentation, task_segment_body, task_segment_part, task_quality

urlpatterns = patterns(
    '',

    url(r'^segmentation$',
        segmentation, name='segmentation.segmentation'),

    url(r'^task$',
        task_segment_body, name='segmentation.task_segment_body'),

    url(r'^part$',
        task_segment_part, name='segmentation.task_segment_part'),

    url(r'^quality$',
        task_quality, name='segmentation.task_quality'),

    url(r'^task/(?P<dataset_id>\w+)$',
        task_segment_body),

    url(r'^part/(?P<dataset_id>\w+)$',
        task_segment_part),

    url(r'^quality/(?P<dataset_id>\w+)$',
        task_quality),
)
