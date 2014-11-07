from django.core.management.base import BaseCommand

import numpy as np

from PIL import Image

import cv2

from pose.models import Person


class Command(BaseCommand):
    help = 'Find person annotations that do not fit in the bounding box.'

    def handle(self, *args, **options):
        # walk through all images and write out a correct person segmentation
        for person in Person.objects.all():
            bounding_box = person.bounding_box

            assert(person.parse_poses.count() == 1)
            points, visible = person.parse_poses.all()[0].visible_end_points()

            points = points[visible, :]

            #import pdb; pdb.set_trace()

            if not (np.all(points[:, 0] >= bounding_box.min_point[0]) and
                    np.all(points[:, 1] >= bounding_box.min_point[1]) and
                    np.all(points[:, 0] < bounding_box.max_point[0]) and
                    np.all(points[:, 1] < bounding_box.max_point[1])):
                print(person.photo.name)

                image = np.asarray(person.photo.open_image())
                for p in range(points.shape[0]):
                    point = np.round(
                        points[p, :] * person.photo.orig_height).astype(np.int)
                    cv2.circle(image,
                               (point[0], point[1]),
                               2,
                               [255, 0, 0])

                Image.fromarray(image).save(
                    'images/{}.jpg'.format(person.photo.name))
