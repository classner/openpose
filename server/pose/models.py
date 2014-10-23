from django.db import models

import json

import numpy as np
import scipy.sparse as sparse

from photos.models import Photo
from common.models import ResultBase

class AABB:
    def __init__(self, min_point, max_point):
        self.min_point = min_point
        self.max_point = max_point

    @property
    def width(self):
        return self.max_point[0] - self.min_point[0]

    @property
    def height(self):
        return self.max_point[1] - self.min_point[1]

    @property
    def x(self):
        return self.min_point[0]

    @property
    def y(self):
        return self.min_point[1]

class Person(ResultBase):
    photo = models.ForeignKey(Photo, related_name='persons')

    bounding_box_data = models.TextField(null=True)

    def __unicode__(self):
        return u'person ' + self.photo.name

    @property
    def bounding_box(self):
        if self.bounding_box_data:
            bounding_box_data = json.loads(self.bounding_box_data)

            return AABB(np.array([bounding_box_data[0], bounding_box_data[1]])
                    , np.array([bounding_box_data[2], bounding_box_data[3]]))
        else:
            return None

    @bounding_box.setter
    def bounding_box(self, bounding_box):
        if bounding_box:
            self.bounding_box_data = json.dumps([
                bounding_box.min_point[0],
                bounding_box.min_point[1],
                bounding_box.max_point[0],
                bounding_box.max_point[1]])
        else:
            self.bounding_box_data = None

    def get_entry_dict(self):
        """ Return a dictionary of this model containing just the fields needed
        for javascript rendering.  """

        # generating thumbnail URLs is slow, so only generate the ones
        # that will definitely be used.
        if self.bounding_box_data:
            bounding_box = json.loads(self.bounding_box_data)
        else:
            bounding_box = None

        return {
                'id': self.id,
                'bounding_box': bounding_box,
                'photo': {
                    'fov': self.photo.fov,
                    'aspect_ratio': self.photo.aspect_ratio,
                    'image': {
                        #'200': self.photo.image_200.url,
                        #'300': self.photo.image_300.url,
                        #'512': self.photo.image_512.url,
                        '1024': self.photo.image_1024.url,
                        '2048': self.photo.image_2048.url,
                        'orig': self.photo.image_orig.url,
                        }
                    }
                }

class ParsePose(ResultBase):
    person = models.ForeignKey(Person, related_name='parse_poses')

    vertices = models.TextField(null=True)
    visible_vertices = models.TextField(null=True)

    def __unicode__(self):
        return u'pose annotation'

    def get_thumb_template(self):
        return 'person/parse_person_thumb.html'

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

    @property
    def visible(self):
        return json.loads(self.visible_vertices)

    @visible.setter
    def visible(self, visible_vertices):
        if len(visible_vertices) != 14:
            raise ValueError('Not enough points')

        self.visible_vertices = json.dumps(visible_vertices)

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

    def visible_end_points(self):
        annotation = np.array(self.pose)
        to_endpoints = ParsePose._build_to_endpoints()
        end_points = to_endpoints.dot(annotation)

        visibility = to_endpoints.dot(np.array(self.visible, dtype=np.float)) > 0.99

        return (end_points, visibility)


