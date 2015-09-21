import numpy as np

import cv2

from pose.models import ParsePose


class PartSegmentation:
    part_index_ = {
        k: v+1
        for (v, k) in enumerate(sorted(ParsePose.part_description.keys()))
        }

    def _clean(self, segmentation):
        # some images are jpegs; binarize them again
        segmentation = (segmentation > 128).astype(np.uint8) * 255

        # run some morphological operators to improve the quality of the
        # segmentation
        kernel = np.ones((2, 2), np.uint8)
        return cv2.morphologyEx(
            cv2.morphologyEx(segmentation, cv2.MORPH_OPEN, kernel),
            cv2.MORPH_CLOSE, kernel)

    def combine(self, parse_pose, segmentation, part_segmentations):
        # the last offset of the aux labels
        label_offset = 2
        dont_know_label = 0
        free_label = 1
        background_label = 2

        segmentation = self._clean(segmentation)

        combined = np.ones_like(segmentation, dtype=np.int32) * free_label

        for part, part_segmentation in part_segmentations.iteritems():
            part_segmentation = self._clean(part_segmentation)

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
