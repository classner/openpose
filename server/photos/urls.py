from django.conf.urls import patterns, url
from photos.views import photo_by_dataset, photo_detail

urlpatterns = patterns(
    '',

    url(r'^$',
        photo_by_dataset, name='photo-by-dataset'),

    url(r'^dataset/(?P<dataset_id>\w+)/$',
        photo_by_dataset, name='photo-by-dataset'),

    url(r'^dataset/(?P<dataset_id>\w+)/(?P<filter_key>\w+)/$',
        photo_by_dataset, name='photo-by-dataset'),

    url(r'^(?P<pk>\d+)/$',
        photo_detail, name='photo-detail'),

)
