from django.db import models

import json

import numpy as np
import scipy.sparse as sparse

from photos.models import Photo
from common.models import ResultBase

class ParsePose(ResultBase):
    photo = models.ForeignKey(Photo, related_name='parse_pose')

    vertices = models.TextField(null=True)

    def __unicode__(self):
        return u'pose annotation'

    def get_thumb_template(self):
        return 'person/parse_person_thumb.html'

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

    @staticmethod
    def _build_to_endpoints():
        i = np.array([1, 1, 2, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16,
            17, 18, 19, 20]) - 1
        j = np.array([9, 10, 3, 4,
            3, 2, 4, 5, 2, 1, 5, 6,
            9, 8, 10, 11, 8, 7, 11, 12,
            14, 13]) - 1
        weight = np.array([0.5, 0.5, 0.5, 0.5,
            1, 1, 1, 1, 1, 1, 1, 1,
            1, 1, 1, 1, 1, 1, 1, 1,
            1, 1])
        return sparse.coo_matrix((weight, (i, j)), shape=(2 * 10,
            14)).tocsr()

    def end_points(self):
        annotation = np.array(self.pose)
        return ParsePose._build_to_endpoints().dot(annotation)


