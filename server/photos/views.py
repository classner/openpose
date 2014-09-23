import json

from django.shortcuts import render, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import ensure_csrf_cookie
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q

from cacheback.decorators import cacheback
from endless_pagination.decorators import page_template
from django.http import Http404

from common.utils import dict_union, \
    json_response, json_success_response
from photos.models import Photo, PhotoDataset

# different ways photos can be filtered
PHOTO_FILTERS = {
    'all': {
        'name': 'Raw input',
        'filter': Photo.DEFAULT_FILTERS
    },
}
# display order
PHOTO_FILTER_KEYS = ['all']


def photo_by_dataset_entries(dataset_id, filter_key):
    """ Returns queryset for each filter """

    photo_filter = PHOTO_FILTERS[filter_key]['filter']
    if dataset_id != 'all':
        photo_filter = dict_union(photo_filter, {
            'dataset_id': dataset_id
        })
    return Photo.objects.filter(**photo_filter)


@cacheback(3600)
def photo_datasets(**filters):
    """ Returns the dataset list along with photo counts """
    datasets = [
        {'id': c.id, 'name': c.name, 'count': c.photo_count(**filters)}
        for c in PhotoDataset.objects.all()
    ]
    datasets = filter(lambda x: x['count'], datasets)
    datasets.sort(key=lambda x: x['count'], reverse=True)

    datasets_all = [
        {'id': 'all', 'name': 'all', 'count': Photo.objects.filter(
            **Photo.DEFAULT_FILTERS
        ).filter(**filters).count()}
    ]

    return {
        'datasets': datasets,
        'datasets_all': datasets_all
    }


@cacheback(300)
def photo_by_dataset_filters(dataset_id):
    """ Returns the list of filters extended with the photo count """
    ret = []
    for k in PHOTO_FILTER_KEYS:
        ret.append(dict_union({
            'key': k,
            'count': photo_by_dataset_entries(dataset_id, k).count(),
        }, PHOTO_FILTERS[k]))
    return ret


@page_template('grid_page.html')
def photo_by_dataset(request, dataset_id='all', filter_key='all',
                      template='photos/by_dataset.html',
                      extra_context=None):

    """ List of photos, filtered by a dataset and optional extra ``filter_key`` """

    if filter_key not in PHOTO_FILTERS:
        raise Http404

    if dataset_id != 'all':
        dataset_id = int(dataset_id)

    entries = photo_by_dataset_entries(dataset_id, filter_key)

    query_filter = {}
    for k, v in request.GET.iteritems():
        if k == u'page' or k == u'querystring_key':
            continue
        elif k == u'publishable':
            query_filter['license__publishable'] = True
        else:
            query_filter[k] = v
    if query_filter:
        entries = entries.filter(**query_filter)

        entries = entries.order_by('-added')

    context = dict_union({
        'nav': 'browse/photo',
        'subnav': 'by-dataset',
        'filter_key': filter_key,
        'dataset_id': dataset_id,
        'filters': photo_by_dataset_filters(dataset_id),
        'url_name': 'photo-by-dataset',
        'entries': entries,
        'entries_per_page': 30,
        'span': 'span3',
        'rowsize': '3',
        'thumb_template': 'photos/thumb.html',
    }, extra_context)

    context.update(photo_datasets())
    return render(request, template, context)


def photo_detail(request, pk):
    photo = get_object_or_404(Photo, pk=pk)

    # sections on the page
    nav_section_keys = [
        ("photo", 'Photo'),
    ]
    nav_sections = [
        {
            'key': t[0],
            'name': t[1],
            'votes': [],
            'template': 'photos/detail/%s.html' % t[0],
        }
        for t in nav_section_keys if t
    ]

    return render(request, 'photos/detail.html', {
        'nav': 'browse/photo',
        'photo': photo,
        'nav_sections': nav_sections,
    })
