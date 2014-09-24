from django.db import models

import json

from photos.models import Photo
from common.models import ResultBase

class ParsePose(ResultBase):
    photo = models.ForeignKey(Photo, related_name='parse_pose')

    vertices = models.TextField(null=True)

    def __unicode__(self):
        return u'pose annotation'

    def get_thumb_template(self):
        return 'submitted_parse_pose_thumb.html'

    def publishable(self):
        return self.photo.publishable()

    @property
    def pose(self):
        """ A list of tuples for each part. """
        return json.loads(self.vertices)

    @pose.setter
    def pose(self, pose_vertices):
        if len(pose_vertices) != 14:
            raise ValueError('Not enough points')
        for point in pose_vertices:
            if len(point) != 2:
                raise ValueError('Only two coordinates are allowed')

        self.vertices = json.dumps(pose_vertices)
