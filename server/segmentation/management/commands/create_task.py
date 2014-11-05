import os
from optparse import make_option

from clint.textui import progress

from django.core.management.base import BaseCommand
from accounts.models import UserProfile

import numpy as np
import scipy.io

import json

from pose.models import Person

class Command(BaseCommand):
    help = 'Create segmentation tasks'

    def handle(self, *args, **options):
        admin_user = UserProfile.objects.get(user__username='admin')

        persons = Person.objects.filter(photo__dataset__name='LSP')

        created_count = 0

        for p in progress.bar(persons):
            # check if this person has a proper segmentation
            correct_full_tasks = p.segmentation_tasks.filter(
                    part__isnull=True,
                    responses__qualities__correct=True).count()

            if correct_full_tasks > 0:
                # check if there is not already a part task that we would like
                # to create
                task, created = p.segmentation_tasks.get_or_create(
                        parse_pose=p.parse_poses.all()[0], part=args[0])

                if created:
                    created_count += 1

        print('created {} new tasks'.format(created_count))
