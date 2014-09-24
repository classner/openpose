from django.db import models

import json

from photos.models import Photo
from common.models import EmptyModelBase, ResultBase

from common.utils import get_content_tuple, recursive_sum

class PersonSegmentation(ResultBase):
    """ Person segmentation submitted by user. """

    photo = models.ForeignKey(Photo, related_name='scribbles')

    # Vertices format: x1,y1,x2,y2,x3,y3,... (coords are fractions of width/height)
    # (this format allows easy embedding into javascript)
    scribbles = models.TextField(null=True)
    # num_vertices should be equal to len(points.split(','))//2
    num_scribbles = models.IntegerField(null=True)

    def __unicode__(self):
        return '%s scribbles in segmentation' % self.num_scribbles

    def get_thumb_template(self):
        return 'submitted_segmentation_thumb.html'

    def publishable(self):
        return self.photo.publishable()

    @staticmethod
    def mturk_submit(user, hit_contents, results, time_ms, time_active_ms,
                     experiment, version, mturk_assignment=None, **kwargs):
        """ Add new instances from a mturk HIT after the user clicks [submit] """

        if unicode(version) != u'1.0':
            raise ValueError("Unknown version: %s" % version)

        photo = hit_contents[0]
        scribbles_list = results[str(photo.id)][u'scribbles']
        time_ms_list = time_ms[str(photo.id)][u'scribbles']
        time_active_ms_list = time_active_ms[str(photo.id)][u'scribbles']

        if len(scribbles_list) != len(time_ms_list):
            raise ValueError("Result length mismatch (%s polygons, %s times)" % (
                len(scribbles_list), len(time_ms_list)))

        slug = experiment.slug
        if slug != u'segment_person':
            raise ValueError("Unknown slug: %s" % slug)

        # store results in SubmittedShape objects
        for scribble in scribbles_list:
            num_vertices = len(scribble)
            if num_vertices % 2 != 0:
                raise ValueError("Odd number of vertices (%d)" % num_vertices)

        new_obj, created = photo.scribbles.get_or_create(
            user=user,
            mturk_assignment=mturk_assignment,
            time_ms=recursive_sum(time_ms),
            time_active_ms=recursive_sum(time_active_ms),
            # (repr gives more float digits)
            scribbles=json.dumps(scribbles_list),
            num_scribbles=len(scribbles_list),
            **kwargs
        )

        if created:
            return {get_content_tuple(photo): [new_obj]}
        else:
            return {}
