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
    args = '<user> <dataset> [<part>]'
    help = 'Create segmentation tasks. If part is not given a full segmentation is created.'

    def handle(self, *args, **options):
        dataset_name = args[1]


        if len(args) < 2:
            print 'Please supply a dataset name and optionally a part name.'
            return
        else:
            username = args[0]
            dataset_name = args[1]
            part = None

            if len(args) == 3:
                part = args[2]
            else:
                print 'Too many arguments.'
                return

        user = UserProfile.objects.get(user__username=username)

        persons = Person.objects.filter(photo__dataset__name=dataset_name)

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
                        parse_pose=p.parse_poses.all()[0], part=part)

                if created:
                    created_count += 1

        print('created {} new tasks'.format(created_count))
