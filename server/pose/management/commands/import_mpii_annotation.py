"""Import MPII dataset pose annotations for the MPII-SEG task."""
# pylint: disable=F0401, C0111, R0914, E1101, R0201, R0903
from clint.textui import progress, puts, colored

from django.core.management.base import BaseCommand
from django.db import transaction
from accounts.models import UserProfile

import numpy as np

from photos.models import PhotoDataset, Photo
from pose.models import AABB

class Command(BaseCommand):  # pylint: disable=W0232

    """MPII Pose annotation addition command."""

    args = '<user> <dataset> <annotation.npz>'
    help = 'Adds pose annotation from the mpii-seg .npz file.'

    def handle(self, *args, **options):  # pylint: disable=W0613
        """Process."""
        if len(args) != 3:
            puts(colored.red('Please specify a user, dataset and annotation '
                             'file!'))
            return
        username, dset_name, ann_filename = args  # pylint: disable=W0632
        admin_user = UserProfile.objects.get(user__username=username)
        annotation_array = np.load(ann_filename)['poses']
        image_name_template = '{0:05d}'

        # Reduce to the LSP annotations and format.
        annotation_array = annotation_array[
            :, range(6) + range(10, 16) + [7, 9], :]

        annotations = annotation_array[0:2, :, :].astype('float')
        visibility = annotation_array[2, :, :].astype('float')

        # Use the visibility flag and 'outsideness; as visibility indicator.
        for pose_idx in range(visibility.shape[1]):
            for joint_idx in range(visibility.shape[0]):
                visibility[joint_idx, pose_idx] = (
                    np.all(annotations[:, joint_idx, pose_idx] >= 0) and
                    visibility[joint_idx, pose_idx] > 0
                )

        dataset, _ = PhotoDataset.objects.get_or_create(name=dset_name)

        for i in progress.bar(xrange(annotations.shape[2])):
            # get the right image from the dataset that is connected to this
            # annotation
            try:
                photo = Photo.objects.get(
                        dataset=dataset,
                        name=image_name_template.format(i + 1),
                        )
            except Photo.DoesNotExist as exc:
                puts(colored.yellow('Not annotating photo {}.{}: {}'.format(
                    dataset,
                    image_name_template.format(i + 1),
                    exc)))
                continue

            bounding_box = AABB(np.array([0, 0]),
                                np.array([photo.aspect_ratio, 1]))

            with transaction.atomic():
                # create a person annotation
                person = photo.persons.create(
                        user=admin_user,
                        bounding_box=bounding_box,
                        )

                annotation = annotations[:, :, i].transpose() \
                        / photo.image_orig.height

                person.parse_poses.create(
                        user=admin_user,
                        pose=annotation.tolist(),
                        visible=visibility[:, i].tolist(),
                        )
