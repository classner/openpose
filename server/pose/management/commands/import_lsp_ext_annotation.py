import os
from optparse import make_option

from clint.textui import progress

from django.core.management.base import BaseCommand
from django.db import transaction
from accounts.models import UserProfile

import numpy as np
import scipy.io

import json

from photos.models import PhotoDataset, FlickrUser, Photo
from pose.models import ParsePose, AABB

class Command(BaseCommand):
    args = '<annotation.mat> <bouding_box.txt>'
    help = 'Adds LSP annotation from MAT'

    def handle(self, *args, **options):
        admin_user = UserProfile.objects.get(user__username='admin')

        annotations_file = scipy.io.loadmat(args[0])

        bounding_box_file = open(args[1], 'r')
        bounding_boxes = [
                np.array(map(float, bounding_box_line.split(' ')[1:]))
                for bounding_box_line in bounding_box_file]

        image_name_template = 'im{0:05d}'

        annotations = np.transpose(annotations_file.get('joints'), [1, 0, 2])[0:2, :, :]

        dataset, _ = PhotoDataset.objects.get_or_create(name='LSP ext')

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
                bounding_box = AABB(np.array([
                    bounding_boxes[i][0] / photo.orig_height,
                    bounding_boxes[i][1] / photo.orig_height]),
                    np.array([
                    bounding_boxes[i][2] / photo.orig_height,
                    bounding_boxes[i][3] / photo.orig_height]))

                with transaction.atomic():
                    # create a person annotation
                    person = photo.persons.create(
                            user=admin_user,
                            bounding_box=bounding_box,
                            )

                    annotation = annotations[:, :, i].transpose() \
                            / photo.image_orig.height

                    person.parse_poses.create(
                            user=admin_user,
                            pose=annotation.tolist(),
                            )
