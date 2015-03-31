import random
import string
import sys
import os.path
from random import choice

from django.core.management.base import BaseCommand
from imagekit.utils import open_image

from clint.textui import progress

import numpy as np

import cv2

import lmdb

from photos.models import Photo


class Command(BaseCommand):
    help = 'Extract a dataset'

    def random_key_(self):
        return ''.join(
            random.choice(string.ascii_uppercase + string.digits)
            for _ in range(6))

    def write_segmentation_(self, caffe, photo, person, tasks, txn):
        # gather all those good segmentations
        segmentations = [response
                         for task in tasks
                         for response in task.responses.filter(
                             qualities__correct=True)]

        # inform the user if we have more than one good solution
        if len(segmentations) > 1:
            print('The photo: {} has more than one good segmentation'
                  .format(photo.name))

        segmentation_file = choice(segmentations).segmentation
        segmentation_image = open_image(segmentation_file)
        segmentation = np.asarray(segmentation_image)
        segmentation_image.close()
        segmentation_file.close()

        # some images are jpegs; binarize them again
        segmentation = (segmentation > 128).astype(np.uint8)

        # run some morphological operators to improve the quality of the
        # segmentation

        kernel = np.ones((2, 2), np.uint8)
        cleaned_segmentation = cv2.morphologyEx(
            cv2.morphologyEx(segmentation, cv2.MORPH_OPEN, kernel),
            cv2.MORPH_CLOSE, kernel)

        # get the context in which this segmentation lies in
        bounding_box = person.bounding_box
        height = photo.orig_height

        scaled_bounding_box = np.round(
            np.array([
                bounding_box.min_point[0],
                bounding_box.min_point[1],
                bounding_box.max_point[0],
                bounding_box.max_point[1]])
            * height).astype(np.int)

        # full_segmentation = np.zeros((height, width))
        # full_segmentation[
        #     scaled_bounding_box[1]:scaled_bounding_box[3],
        #     scaled_bounding_box[0]:scaled_bounding_box[2]
        # ] = cleaned_segmentation

        # Only take the part of the image that contains the person.
        image_file = open_image(photo.image_orig)
        image = np.asarray(image_file)[
            scaled_bounding_box[1]:scaled_bounding_box[3],
            scaled_bounding_box[0]:scaled_bounding_box[2]
        ]
        image_file.close()
        photo.image_orig.close()

        input = np.transpose(
            np.concatenate((image, cleaned_segmentation[:, :, None]),
                           axis=2),
            [2, 0, 1])

        datum = caffe.io.array_to_datum(input)
        txn.put(self.random_key_() + str(photo.name),
                datum.SerializeToString(),
                overwrite=False)

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

        with open(include_list_path, 'r') as list_file:
            for photo_name in progress.bar(list_file.readlines()):
                photo_name = photo_name.rstrip()
                photo = Photo.objects.get(dataset__name=dataset_name,
                                          name=photo_name)

                # XXX for now we'll assume that we have one person per image
                assert(photo.persons.count() == 1)

                person = photo.persons.all()[0]
                tasks = person.segmentation_tasks.filter(
                    # full body segmentation
                    part__isnull=True,
                    # at least one person thinks this is correct
                    responses__qualities__correct=True,
                )

                if not tasks:
                    print('exclude: {}'.format(photo.name))
                    continue

                self.write_segmentation_(caffe, photo, person, tasks, txn)

                transactions += 1

                if transactions > 300:
                    txn.commit()
                    transactions = 0
                    txn = db.begin(write=True)

        if transactions > 0:
            txn.commit()

        db.close()
