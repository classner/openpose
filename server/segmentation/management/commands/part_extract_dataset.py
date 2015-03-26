import os.path
from random import choice

from django.core.management.base import BaseCommand
from imagekit.utils import open_image

from clint.textui import progress

import numpy as np

import cv2

from PIL import Image

import h5py

from photos.models import PhotoDataset
from pose.models import ParsePose


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

        segmentation = np.asarray(open_image(
            choice(segmentations).segmentation))

        # some images are jpegs; binarize them again
        segmentation = (segmentation > 128).astype(np.uint8) * 255

        # run some morphological operators to improve the quality of the
        # segmentation
        kernel = np.ones((2, 2), np.uint8)
        cleaned_segmentation = cv2.morphologyEx(
            cv2.morphologyEx(segmentation, cv2.MORPH_OPEN, kernel),
            cv2.MORPH_CLOSE, kernel)

        return cleaned_segmentation

    part_index_ = {
        k: v+1
        for (v, k) in enumerate(sorted(ParsePose.part_description.keys()))
        }

    def fiddle_part_segmentation_(self, parse_pose, segmentation,
                                  part_segmentations):
        # the last offset of the aux labels
        label_offset = 2
        dont_know_label = 0
        free_label = 1
        background_label = 2

        combined = np.ones_like(segmentation, dtype=np.int32) * free_label

        for part, part_segmentation in part_segmentations.iteritems():
            free = np.logical_and(combined == free_label,
                                  part_segmentation > 0)
            occupied = np.logical_and(combined != free_label,
                                      part_segmentation > 0)

            # set already occupied part to `don't know'
            combined[occupied] = dont_know_label

            # everything else to the new label
            combined[free] = self.part_index_[part] + label_offset

        # set everything that is masked in the segmentation as background to
        # background
        combined[segmentation == 0] = background_label

        (torso_stick, visible) = parse_pose.visible_part_end_points(
            ParsePose.PART_TORSO)

        torso_center = np.round(
            np.mean(torso_stick, axis=0) * segmentation.shape[0]
            ).astype(np.int)

        # find the connected component around the the torso_center
        mask = np.ones((combined.shape[0] + 2, combined.shape[1] + 2),
                       dtype=np.uint8)
        mask[1:-1, 1:-1] = combined != free_label
        cv2.floodFill(combined, mask,
                      (torso_center[0], torso_center[1]),
                      self.part_index_[ParsePose.PART_TORSO] + label_offset)

        # everything that is still free -> dont_know_label
        combined[combined == free_label] = dont_know_label

        # do a watershed to extend everything into the unknown region
        borders = np.zeros(
            (segmentation.shape[0], segmentation.shape[1], 3),
            dtype=np.uint8)
        cv2.watershed(borders, combined)

        # fill the border pixels
        # we count the labels in a neighborhood around the pixel to find the
        # most likely label
        combined[combined == -1] = free_label
        y, x = np.where(np.logical_or(
            combined == free_label,
            combined == dont_know_label))
        neighborhood = np.array([[-1, -1], [-1, 1], [1, -1], [1, 1]])
        for p in np.vstack((y, x)).transpose():
            points = neighborhood + p

            points[:, 0] = np.minimum(
                np.maximum(points[:, 0], 0), combined.shape[0] - 1)
            points[:, 1] = np.minimum(
                np.maximum(points[:, 1], 0), combined.shape[1] - 1)

            v = combined[points[:, 0], points[:, 1]]
            counts = np.bincount(v)
            # remove the free_label and dont_know_label
            if len(counts) > dont_know_label:
                counts[dont_know_label] = 0
            if len(counts) > free_label:
                counts[free_label] = 0

            # this might brake in weird situations where there are a lot of
            # frees and dont_knows clustered together, increase the
            # neighborhood in this case
            assert(sum(counts) > 0)
            combined[p[0], p[1]] = np.argmax(counts)

        assert(np.all(combined != free_label))
        assert(np.all(combined != dont_know_label))

        combined[combined == 0] = background_label

        return combined.astype(np.uint8) - background_label

    def handle(self, *args, **options):
        dataset_name = args[0]
        output_folder = args[1]

        photos = PhotoDataset.objects.get(name=dataset_name).photos.all()

        # walk through all images and write out a correct person segmentation
        print(self.part_index_)
        for photo in progress.bar(photos):
            # XXX for now we'll assume that we have one person per image
            assert(photo.persons.count() == 1)

            person = photo.persons.all()[0]

            assert(person.parse_poses.count() == 1)
            parse_pose = person.parse_poses.all()[0]

            all_tasks = person.segmentation_tasks.all()

            segmentation = self.correct_segmentation_(photo.name, all_tasks)

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

            segmentation = self.fiddle_part_segmentation_(
                parse_pose, segmentation, part_segmentations)

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

            colors = (np.array([
                [0, 0, 0],
                [0.80, 0.47, 0.65],
                [0, 0.62, 0.45],
                [0.34, 0.71, 0.91],
                [0.84, 0.37, 0],
                [0, 0.45, 0.70],
                [0.97, 0.93, 0.35],
            ]) * 255).astype(np.uint8)

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

            Image.fromarray(colors[segmentation]).save(
                os.path.join(output_folder, '{}.png'.format(photo.name)))

            Image.open(photo.image_orig).save(
                os.path.join(output_folder, '{}.orig.png'.format(photo.name)))

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
                ] = segmentation

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
        print(self.part_index_)
