import os.path
from random import choice

from django.core.management.base import BaseCommand
from imagekit.utils import open_image

from clint.textui import progress

import numpy as np

import cv2

import h5py

from photos.models import PhotoDataset


class Command(BaseCommand):
    help = 'Extract a dataset'

    def handle(self, *args, **options):
        dataset_name = args[0]
        output_folder = args[1]

        photos = PhotoDataset.objects.get(name=dataset_name).photos.all()

        # walk through all images and write out a correct person segmentation
        for photo in progress.bar(photos):
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

            # gather all those good segmentations
            segmentations = [response
                             for task in tasks
                             for response in task.responses.filter(
                                 qualities__correct=True)]

            # inform the user if we have more than one good solution
            if len(segmentations) > 1:
                print('The photo: {} has more than one good segmentation'
                      .format(photo.name))

            segmentation = np.asarray(open_image(
                choice(segmentations).segmentation))

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
            width = photo.orig_width
            height = photo.orig_height

            scaled_bounding_box = np.round(np.array([
                bounding_box.min_point[0],
                bounding_box.min_point[1],
                bounding_box.max_point[0],
                bounding_box.max_point[1]])
                * height).astype(np.int)

            full_segmentation = np.zeros((height, width))
            full_segmentation[
                scaled_bounding_box[1]:scaled_bounding_box[3],
                scaled_bounding_box[0]:scaled_bounding_box[2]
                ] = cleaned_segmentation

            segmentation_file = h5py.File(
                os.path.join(output_folder,
                             '{}.segmentation.h5'.format(photo.name)), 'w')
            segmentation_file.create_dataset(
                '/segmentation',
                data=full_segmentation.transpose([1, 0]),
                compression='gzip', compression_opts=6,
                dtype=np.uint8)
            segmentation_file.close()
