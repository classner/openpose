import os
from optparse import make_option

from clint.textui import progress

from django.core.management.base import BaseCommand
from accounts.models import UserProfile

import numpy as np
import scipy.io

import json

from mturk.models import Experiment, PendingContent

from segmentation.models import PersonSegmentationTask

class Command(BaseCommand):
    help = 'Create segmentation tasks'

    def handle(self, *args, **options):
        user = UserProfile.objects.get(user__username='peter')
        experiment = Experiment.objects.get(slug='segment_part_person')

        tasks = PersonSegmentationTask.objects.filter(part__isnull=False, user=user)

        id_list_fail = [task.id for task in tasks]

        pc_to_expire = PendingContent.objects.filter(experiment=experiment, num_outputs_max__gt=0, object_id__in=id_list_fail)

        pc_to_expire.update(num_outputs_max=0)
