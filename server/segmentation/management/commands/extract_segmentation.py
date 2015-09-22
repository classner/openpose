import os.path
import json
from random import choice

from django.core.management.base import BaseCommand
from imagekit.utils import open_image

from clint.textui import progress

import numpy as np

from PIL import Image

from photos.models import Photo
from pose.models import ParsePose

from part_segmentation import PartSegmentation


class Command(BaseCommand):
    args = '<dataset> <file-list-file> <output-folder>'
    help = 'Extract a dataset'

    def correct_segmentation_(self, photo_name, all_tasks, part=None):
        tasks = all_tasks.filter(
            # full body segmentation
            part=part,
            # at least one person thinks this is correct
            responses__qualities__correct=True,
            )

        if not tasks:
            return None

        # gather all those good segmentations
        segmentations = [response
                         for task in tasks
                         for response in task.responses.filter(
                             qualities__correct=True)]

        # inform the user if we have more than one good solution
        if len(segmentations) > 1:
            print('The photo: {} has more than one good segmentation'
                  .format(photo_name))

        segmentation_file = choice(segmentations).segmentation
        segmentation_image = open_image(segmentation_file)
        segmentation = np.asarray(segmentation_image)
        segmentation_image.close()
        segmentation_file.close()

        return segmentation

    def handle(self, *args, **options):
        if len(args) != 3:
            print 'Please, suppy a dataset name, file containing a newline-separated list of name'
            print 'and an output folder.'
            return

        dataset_name = args[0]
        include_list_path = args[1]
        output_path = args[2]

        processor = PartSegmentation()

        annotation_file = open(os.path.join(output_path,
                                            'annotations.txt'), 'w+')
        bb_file = open(os.path.join(output_path,
                                    'bb.txt'), 'w+')

        # walk through all images and write out a correct person segmentation
        with open(include_list_path, 'r') as list_file:
            for photo_name in progress.bar(list_file.readlines()):
                photo_name = photo_name.rstrip()
                photo = Photo.objects.get(dataset__name=dataset_name,
                                          name=photo_name)

                # XXX for now we'll assume that we have one person per image
                assert(photo.persons.count() == 1)

                person = photo.persons.all()[0]


                all_tasks = person.segmentation_tasks.all()

                segmentation = self.correct_segmentation_(photo.name,
                                                          all_tasks)

                part_segmentations = {}
                for part in ParsePose.part_description:
                    # we treat the torse differently
                    # it should be able to infer it from the rest of the parts
                    if part == ParsePose.PART_TORSO:
                        continue

                    part_segmentations[part] = self.correct_segmentation_(
                        photo.name, all_tasks, part)

                if segmentation is None:
                    print('exclude: {}'.format(photo.name))
                    continue

                # Write person segmentation.
                Image.fromarray(segmentation).save(
                    os.path.join(output_path, photo.name)
                    + '_segmentation.png')

                if person.parse_poses.count():
                    # Write part segmentation if we've got a valid one.
                    if not any(map(lambda s: s is None,
                                part_segmentations.values())):
                        part_segmentation = processor.combine(
                            parse_pose, segmentation, part_segmentations)
                        Image.fromarray(part_segmentation).save(
                            os.path.join(output_path, photo.name)
                            + '_part_segmentation.png')

                    # Write pose annotation.
                    annotation_file.write('{}: {}\n'.format(
                        photo.name, parse_pose.pose))
                bb_file.write('{}: {}\n'.format(
                    photo.name, json.loads(person.bounding_box_data)))

        annotation_file.close()
        bb_file.close()
