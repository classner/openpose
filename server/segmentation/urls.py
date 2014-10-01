from django.conf.urls import patterns, url
from segmentation.views import segmentation, task

urlpatterns = patterns(
    '',

    url(r'^segmentation$',
        segmentation, name='segmentation.segmentation'),

    url(r'^task$',
        task, name='segmentation.task'),

    url(r'^task/(?P<dataset_id>\w+)$',
        task),
)
