import sys
import os.path
from random import choice

from django.core.management.base import BaseCommand
from imagekit.utils import open_image

from clint.textui import progress

import numpy as np

import lmdb

from photos.models import Photo
from pose.models import ParsePose

from part_segmentation import PartSegmentation


class Command(BaseCommand):
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

    def write_segmentation_(self, caffe, photo, person, segmentation, txn):
        # get the context in which this segmentation lies in
        bounding_box = person.bounding_box
        height = photo.orig_height

        scaled_bounding_box = np.round(np.array([
            bounding_box.min_point[0],
            bounding_box.min_point[1],
            bounding_box.max_point[0],
            bounding_box.max_point[1]])
            * height).astype(np.int)

        image_file = open_image(photo.image_orig)
        image = np.asarray(image_file)[
            scaled_bounding_box[1]:scaled_bounding_box[3],
            scaled_bounding_box[0]:scaled_bounding_box[2]
        ]
        image_file.close()
        photo.image_orig.close()

        input = np.transpose(
            np.concatenate((image, segmentation[:, :, None]),
                           axis=2),
            [2, 0, 1])

        datum = caffe.io.array_to_datum(input)
        txn.put(str(photo.name), datum.SerializeToString(), overwrite=False)

    def handle(self, *args, **options):
        caffe_root = args[0]
        dataset_name = args[1]
        include_list_path = args[2]
        db_path = args[3]

        # Load caffe
        sys.path.insert(0, os.path.join(caffe_root, 'python'))
        import caffe

        # Get LMDB file database up and running
        db = lmdb.open(db_path, map_size=int(1e12))
        txn = db.begin(write=True)
        transactions = 0

        processor = PartSegmentation()

        # walk through all images and write out a correct person segmentation
        with open(include_list_path, 'r') as list_file:
            for photo_name in progress.bar(list_file.readlines()):
                photo_name = photo_name.rstrip()
                photo = Photo.objects.get(dataset__name=dataset_name,
                                          name=photo_name)

                # XXX for now we'll assume that we have one person per image
                assert(photo.persons.count() == 1)

                person = photo.persons.all()[0]

                assert(person.parse_poses.count() == 1)
                parse_pose = person.parse_poses.all()[0]

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

                if segmentation is None or any(
                        map(lambda s: s is None, part_segmentations.values())):
                    print('exclude: {}'.format(photo.name))
                    continue

                segmentation = processor.combine(
                    parse_pose, segmentation, part_segmentations)

                self.write_segmentation_(caffe, photo, person, segmentation,
                                         txn)

                transactions += 1

                if transactions > 300:
                    txn.commit()
                    transactions = 0
                    txn = db.begin(write=True)

        if transactions > 0:
            txn.commit()

        db.close()
        print(self.part_index_)

        # colors = (np.array([
        #     [0, 0, 0],
        #     [0, 0, 0],
        #     [0.90, 0.62, 0],
        #     [0.34, 0.71, 0.91],
        #     [0, 0.62, 0.45],
        #     [0.97, 0.93, 0.35],
        #     [0, 0.45, 0.70],
        #     [0.84, 0.37, 0],
        #     [0.80, 0.47, 0.65],
        #     [0.52, 0.56, 0.66]
        # ]) * 255).astype(np.uint8)

        # colors = (np.array([
        #     [0, 0, 0],
        #     [0.80, 0.47, 0.65],
        #     [0, 0.62, 0.45],
        #     [0.34, 0.71, 0.91],
        #     [0.84, 0.37, 0],
        #     [0, 0.45, 0.70],
        #     [0.97, 0.93, 0.35],
        # ]) * 255).astype(np.uint8)

        # (orange "#e69f00")
        # (skyblue "#56b4e9")
        # (bluegreen "#009e73")
        # (yellow "#f8ec59")
        # (blue "#0072b2")
        # (vermillion "#d55e00")
        # (redpurple "#cc79a7")
        # (bluegray "#848ea9"))

        # colors = (np.array([
        #     [0, 0, 0],
        #     [0, 0, 0],
        #     [0, 0.4717, 0.4604],
        #     [0.4906, 0, 0],
        #     [1.0, 0.6, 0.2],
        #     [0, 0, 0.509],
        #     [0.2, 0.2, 0.2],
        #     [0.5, 0.5, 0.5],
        #     ]) * 255).astype(np.uint8)

        # Image.fromarray(colors[segmentation]).save(
        #     os.path.join(output_folder, '{}.png'.format(photo.name)))

        # Image.open(photo.image_orig).save(
        #     os.path.join(output_folder, '{}.orig.png'.format(photo.name)))

        # full_segmentation = np.zeros((height, width))
        # full_segmentation[
        #     scaled_bounding_box[1]:scaled_bounding_box[3],
        #     scaled_bounding_box[0]:scaled_bounding_box[2]
        #     ] = segmentation

        # segmentation_file = h5py.File(
        #     os.path.join(output_folder,
        #                  '{}.part_segmentation.h5'.format(photo.name)
        #                  ), 'w')
        # segmentation_file.create_dataset(
        #     '/part_segmentation',
        #     data=segmentation.transpose([1, 0]),
        #     compression='gzip', compression_opts=6,
        #     dtype=np.uint8)
        # segmentation_file.close()
