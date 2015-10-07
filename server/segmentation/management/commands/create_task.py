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
    args = '<user> <dataset>'
    help = 'Create segmentation tasks. If part is not given a full segmentation is created.'

    def handle(self, *args, **options):
        dataset_name = args[1]

        if len(args) != 2:
            print 'Please supply a user and a dataset name.'
            return
        else:
            username = args[0]
            dataset_name = args[1]

        # user = UserProfile.objects.get(user__username=username)

        persons = Person.objects.filter(photo__dataset__name=dataset_name)

        created_count = 0

        for p in progress.bar(persons):
            # check if this person already has a task
            if p.segmentation_tasks.count() == 0:
                p.segmentation_tasks.create(# user=user,
                                            part=None)
                created_count += 1

        print('created {} new tasks'.format(created_count))
