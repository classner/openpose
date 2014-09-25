import os
from optparse import make_option

from clint.textui import progress

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

import numpy as np
import scipy.io

from photos.models import PhotoDataset, FlickrUser, Photo
from pose.models import ParsePose

class Command(BaseCommand):
    args = '<annotation.mat>'
    help = 'Adds LSP annotation from MAT'

    option_list = BaseCommand.option_list + (
        make_option(
            '--delete',
            action='store_true',
            dest='delete',
            default=False,
            help='Delete photos after they are visited'),
    )

    def handle(self, *args, **options):
        admin_user = User.objects.get_or_create(
            username='admin')[0].get_profile()

        annotations_file = scipy.io.loadmat(args[0])

        image_name_template = 'im{0:04d}'

        annotations = annotations_file.get('joints')[0:2, :, :]

        for i in progress.bar(xrange(annotations.shape[2])):
            # get the right image from the dataset that is connected to this
            # annotation
            try:
                photo = Photo.objects.get(name=image_name_template.format(i + 1))

                parse_annotation = ParsePose(
                        user=admin_user,
                        photo=photo,
                        )

                annotation = annotations[:, :, i].transpose() \
                        / np.max([photo.image_orig.width,
                            photo.image_orig.height])
                parse_annotation.pose = annotation.tolist()
                parse_annotation.save()
            except Photo.DoesNotExist as e:
                print '\nNot annotating photo: ', e
