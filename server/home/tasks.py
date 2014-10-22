from celery import shared_task

from django.conf import settings
from django.db.models import Sum
from django.core.cache import get_cache

from photos.models import Photo
from mturk.models import MtAssignment, MtSubmittedContent
from common.utils import dict_union


@shared_task
def update_index_context_task():

    data = {
        'num_assignments_good': MtAssignment.objects.filter(hit__sandbox=False, status='A').count(),
        'num_assignments_all': MtAssignment.objects.filter(hit__sandbox=False, status__isnull=False).count(),

        'num_submitted_all': MtSubmittedContent.objects.filter(assignment__hit__sandbox=False).count(),

        'num_users_good': MtAssignment.objects.filter(hit__sandbox=False, status__isnull=False, worker__blocked=False).distinct('worker').count(),
        'num_users_all': MtAssignment.objects.filter(hit__sandbox=False, status__isnull=False).distinct('worker').count(),

        'num_hours_all': MtAssignment.objects.filter(hit__sandbox=False).aggregate(s=Sum('time_ms'))['s'] / 3600000,
    }

    if settings.ENABLE_CACHING:
        get_cache('persistent').set('home.index_context', data, timeout=None)
    return data
