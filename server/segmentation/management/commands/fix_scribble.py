import os
from optparse import make_option

from clint.textui import progress

import json

from django.core.management.base import BaseCommand

from segmentation.models import PersonSegmentation

class Command(BaseCommand):
    help = 'Fix scribbles to the new format.'

    def handle(self, *args, **options):
        segmentations = PersonSegmentation.objects.all()

        for segmentation in progress.bar(segmentations):
            width = segmentation.photo.orig_width
            height = segmentation.photo.orig_height

            scribbles = json.loads(segmentation.scribbles)

            old_factor = max(width, height)
            new_factor = height

            for scribble in scribbles:
                for point in scribble[u'points']:
                    point[0] = point[0] * old_factor / new_factor
                    point[1] = point[1] * old_factor / new_factor

            segmentation.save()
