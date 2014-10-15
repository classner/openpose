import os
from optparse import make_option

from clint.textui import progress

import json

from django.core.management.base import BaseCommand

from pose.models import ParsePose

import numpy as np

class Command(BaseCommand):
    help = 'Fix scribbles to the new format.'

    def handle(self, *args, **options):
        poses = ParsePose.objects.all()

        for pose in progress.bar(poses):
            width = pose.photo.orig_width
            height = pose.photo.orig_height

            old_factor = float(max(width, height))
            new_factor = float(height)

            pose.pose = (np.array(pose.pose) * old_factor / new_factor).tolist()

            pose.save()
