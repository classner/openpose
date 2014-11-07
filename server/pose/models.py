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


class PartDescription:
    def __init__(self, description, sticks):
        self.description = description
        self.sticks = np.array(sticks)


class ParsePose(ResultBase):
    person = models.ForeignKey(Person, related_name='parse_poses')

    vertices = models.TextField(null=True)
    visible_vertices = models.TextField(null=True)

    person_centric = models.BooleanField(default=True)

    PART_HEAD =      'H'
    PART_ARM_LEFT =  'AL'
    PART_ARM_RIGHT = 'AR'
    PART_TORSO =     'T'
    PART_LEG_LEFT =  'LL'
    PART_LEG_RIGHT = 'LR'

    part_description = {
        PART_HEAD:      PartDescription('head',                   [9]),
        PART_ARM_LEFT:  PartDescription('left arm + left hand',   [8, 6]),
        PART_ARM_RIGHT: PartDescription('right arm + right hand', [7, 5]),
        PART_TORSO:     PartDescription('torso',                  [0]),
        PART_LEG_LEFT:  PartDescription('left leg + left foot',   [4, 2]),
        PART_LEG_RIGHT: PartDescription('right leg + right foot', [3, 1]),
        }

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

    def _points_from_sticks(self, sticks):
        # replicate every index
        end_point_indexes = np.kron(sticks * 2, np.array([1, 1]))
        # get the second endpoint by increasing every second index
        end_point_indexes[1::2] += 1

        end_points, visibility = self.visible_end_points()

        return (end_points[end_point_indexes, :],
                visibility[end_point_indexes])

    def visible_part_end_points(self, part=None):
        if part:
            return self._points_from_sticks(self.part_description[part].sticks)
        else:
            return self.visible_end_points()

    def visible_end_points(self):
        annotation = np.array(self.pose)
        to_endpoints = ParsePose._build_to_endpoints()
        end_points = to_endpoints.dot(annotation)

        visibility = to_endpoints.dot(
            np.array(self.visible, dtype=np.float)) > 0.99

        return (end_points, visibility)


