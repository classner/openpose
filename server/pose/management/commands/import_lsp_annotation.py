import os
from optparse import make_option

from clint.textui import progress

from django.core.management.base import BaseCommand
from accounts.models import UserProfile

import numpy as np
import scipy.io

import json

from photos.models import PhotoDataset, FlickrUser, Photo
from pose.models import ParsePose

class Command(BaseCommand):
    args = '<annotation.mat>'
    help = 'Adds LSP annotation from MAT'

    def handle(self, *args, **options):
        admin_user = UserProfile.objects.get(user__username='admin')

        annotations_file = scipy.io.loadmat(args[0])

        image_name_template = 'im{0:04d}'

        annotations = annotations_file.get('joints')[0:2, :, :]

        dataset, _ = PhotoDataset.objects.get_or_create(name='LSP')

        for i in progress.bar(xrange(annotations.shape[2])):
            # get the right image from the dataset that is connected to this
            # annotation
            photo = None
            try:
                photo = Photo.objects.get(
                        dataset=dataset,
                        name=image_name_template.format(i + 1),
                        )
            except Photo.DoesNotExist as e:
                print '\nNot annotating photo: ', e

            if photo:
                # create a person annotation
                person = photo.persons.create(
                        user=admin_user,
                        bounding_box_dict={
                            'x': 0, 'y': 0,
                            'width': photo.aspect_ratio,
                            'height': 1
                            },
                        )

                annotation = annotations[:, :, i].transpose() \
                        / photo.image_orig.height

                person.parse_pose.create(
                        user=admin_user,
                        pose=annotation.tolist(),
                        )
