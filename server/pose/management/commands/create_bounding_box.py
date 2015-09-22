import os
from optparse import make_option

from clint.textui import progress

from django.core.management.base import BaseCommand
from accounts.models import UserProfile

import numpy as np

import json

from photos.models import PhotoDataset, FlickrUser, Photo
from pose.models import ParsePose, AABB

class Command(BaseCommand):
    args = '<user> <dataset>'
    help = 'Adds LSP annotation from MAT'

    def handle(self, *args, **options):
        if len(args) != 2:
            print 'Please supply a user and a dataset name.'
            return

        username = args[0]
        dataset_name = args[1]

        user = UserProfile.objects.get(user__username=username)

        photos = Photo.objects.filter(dataset__name=dataset_name)

        for photo in progress.bar(photos):
            bounding_box = AABB(np.array([0, 0]),
                                np.array([photo.aspect_ratio, 1]))
            # create a person annotation
            person = photo.persons.create(
                user=user,
                bounding_box=bounding_box,
            )
