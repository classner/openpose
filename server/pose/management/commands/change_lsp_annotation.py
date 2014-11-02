import os
from optparse import make_option

from clint.textui import progress

from django.core.management.base import BaseCommand
from accounts.models import UserProfile

import numpy as np
import scipy.io

import json

from photos.models import PhotoDataset, FlickrUser, Photo
from pose.models import ParsePose, AABB

class Command(BaseCommand):
    args = '<annotation.mat>'
    help = 'Adds LSP annotation from MAT'

    def handle(self, *args, **options):
        admin_user = UserProfile.objects.get(user__username='admin')

        annotations_file = scipy.io.loadmat(args[0])

        image_name_template = 'im{0:04d}'

        annotations = annotations_file.get('joints')[0:2, :, :]

        dataset = PhotoDataset.objects.get(name='LSP')

        for i in progress.bar(xrange(annotations.shape[2])):
            # get the right image from the dataset that is connected to this
            # annotation
            photo = None
            photo = Photo.objects.get(
                    dataset=dataset,
                    name=image_name_template.format(i + 1),
                    )

            annotation = annotations[:, :, i].transpose() \
                    / photo.image_orig.height

            # make sure there is only one pose annotation
            assert(photo.persons.count() == 1)
            person = photo.persons.all()[0]

            assert(person.parse_poses.count() == 1)
            pose_annotation = person.parse_poses.all()[0]

            pose_annotation.pose = annotation.tolist()

            pose_annotation.save()
