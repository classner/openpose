from django.core.management.base import BaseCommand

import numpy as np

from photos.models import Photo
from pose.models import AABB


class Command(BaseCommand):
    help = 'Fix bounding boxes.'

    def handle(self, *args, **options):
        bounding_box_file = open(args[0], 'r')

        entries = [
            bounding_box_line.split(' ')
            for bounding_box_line in bounding_box_file]

        bounding_boxes = [
            (entry[0], np.array(map(float, entry[1:])))
            for entry in entries
            ]

        for img_name, raw_bounding_box in bounding_boxes:
            print(img_name)
            photo = None
            try:
                photo = Photo.objects.get(
                    name=img_name,
                    )
            except Photo.DoesNotExist as e:
                print('\nNot annotating photo: ' + str(e))

            if photo:
                print(photo)
                bounding_box = AABB(
                    np.array([raw_bounding_box[0] / photo.orig_height,
                              raw_bounding_box[1] / photo.orig_height]),
                    np.array([raw_bounding_box[2] / photo.orig_height,
                              raw_bounding_box[3] / photo.orig_height]))

                # grow the bouding box; they mostly seem to be too small
                grow = 0.2
                width = bounding_box.width
                height = bounding_box.height
                bounding_box.min_point[0] = max(
                    0, bounding_box.min_point[0] - width * grow)
                bounding_box.min_point[1] = max(
                    0, bounding_box.min_point[1] - height * grow)
                bounding_box.max_point[0] = min(
                    photo.aspect_ratio,
                    bounding_box.max_point[0] + width * grow)
                bounding_box.max_point[1] = min(
                    1, bounding_box.max_point[1] + height * grow)

                assert(photo.persons.count() == 1)

                person = photo.persons.all()[0]
                person.bounding_box = bounding_box
                person.save()

                # invalidate any segmentation
                for task in person.segmentation_tasks.all():
                    for response in task.responses.all():
                        q = response.qualities.all()

                        if q:
                            q.update(
                                correct=False,
                                canttell=False
                                )
                        else:
                            response.qualities.create(
                                correct=False,
                                canttell=False
                                )
