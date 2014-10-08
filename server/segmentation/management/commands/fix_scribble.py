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

            old_factor = float(max(width, height))
            new_factor = float(height)

            for i in xrange(len(scribbles)):
                for j in xrange(len(scribbles[i][u'points'])):
                    scribbles[i][u'points'][j][0] *= old_factor / new_factor
                    scribbles[i][u'points'][j][1] *= old_factor / new_factor

            new_scribbles = json.dumps(scribbles)

            segmentation.scribbles = new_scribbles

            segmentation.save()
