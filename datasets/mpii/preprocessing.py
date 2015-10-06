"""Do the preprocessing for the MPII datset."""
# pylint: disable=C0103, E1101

from __future__ import print_function

import os
import csv
import numpy as np
import scipy.io
import cv2

DSET_FOLDER = '/is/ps2/classner/caffe/data/mpii/'
MAT = scipy.io.loadmat(os.path.join(DSET_FOLDER,
                       'mpii_human_pose_v1_u12_1/mpii_human_pose_v1_u12_1.mat'))
TARGET_DSET_FOLDER = '/is/ps2/classner/caffe/data/mpii-seg/'

print(type(MAT['RELEASE'][0, 0]['annolist'][0, 0]))
print(MAT['RELEASE'][0, 0]['act'][:, 0].shape)

ACTS = MAT['RELEASE'][0, 0]['act'][:, 0]
TRAIN_TEST = MAT['RELEASE'][0, 0]['img_train'][0]
POS_ANNOTS = MAT['RELEASE'][0, 0]['annolist'][0]
SINGLE_ANNOTS = MAT['RELEASE'][0, 0]['single_person']
# The internal structure of the activity storage is
#
# * category name: act[0][0]
# * activity name: act[1][0]
# * activity id: act[2][0, 0]
#
# Multiple activity ids get merged together to one activity. In the training
# set, there are 397 activities, the rest is only present in the test set.
activities = {}
actnames = []
for act_idx, act in enumerate(ACTS):
    if act[2][0, 0] == -1:
        continue
    act_idn = act[1][0]  # act[0][0] + act[1][0]
    if act_idn not in activities:
        print('New activity detected: {}.'.format(act_idn))
        activities[act_idn] = []
        actnames.append(act[1][0])
    if TRAIN_TEST[act_idx] == 1:
        if os.path.exists(os.path.join(DSET_FOLDER, 'images',
                                       POS_ANNOTS[act_idx][0][0, 0][0][0])):
            if SINGLE_ANNOTS[act_idx][0].shape[0] > 0:
                try:
                    # Check whether pose annotation is availabe.
                    _ = POS_ANNOTS['annorect'][act_idx]['annopoints']\
                        [0, 0][0, 0]['point'][0]['x']
                    _ = POS_ANNOTS['annorect'][act_idx]['annopoints']\
                        [0, 0][0, 0]['point'][0]['y']
                    activities[act_idn].append(act_idx)
                except ValueError:
                    pass
        else:
            print("Missing image: {}!".format(
                POS_ANNOTS[act_idx][0][0, 0][0][0]))

print(len(activities))
print(os.linesep.join(activities.keys()))

for actkey, actval in activities.items():
    print(len(actval))

# There are some activities, for which there is less than three samples in
# the training set. Omit these.
selected_activities = []
for act_name in activities.keys():
    if len(activities[act_name]) >= 5:
        selected_activities.append(act_name)

print('Number of activities with at least 5 samples:', len(selected_activities))
# 202 stay. That's fine!
# Sample 3 images from each.
np.random.seed(42)
sampled_ids = {}
for act_name in selected_activities:
    sampled_ids[act_name] = np.random.permutation(activities[act_name])[:5]

# Copy these images to a folder with restricted structure for easier handling.
correspondance_file = open(os.path.join(TARGET_DSET_FOLDER,
                                        'correspondances.csv'), 'w')
correspondance_csv = csv.writer(correspondance_file)
correspondance_csv.writerow(['mpii_id', 'mpii_name', 'image_name'])
poses = []
running_idx = 1
for act_name in sampled_ids.keys():
    for sample_id in sampled_ids[act_name]:
        image_name = os.path.join(DSET_FOLDER, 'images',
                                  POS_ANNOTS[sample_id][0][0, 0][0][0])
        target_name = os.path.join(TARGET_DSET_FOLDER, 'images',
                                   '{0:05d}.jpg'.format(running_idx))
        correspondance_csv.writerow([sample_id,
                                     POS_ANNOTS[sample_id][0][0, 0][0][0],
                                     '{0:05d}.jpg'.format(running_idx)])
        image = cv2.imread(image_name)
        pose = np.ones((3, 16, 1), dtype='int') * -1
        # Account for MATLAB indexing.
        for info_idx in range(POS_ANNOTS['annorect'][sample_id]['annopoints']\
                                [0, 0][0, 0]['point'][0].shape[0]):
            joint_idx = POS_ANNOTS['annorect'][sample_id]['annopoints']\
                            [0, 0][0, 0]['point'][0]['id'][info_idx][0, 0]
            pose[0, joint_idx, 0] = \
                POS_ANNOTS['annorect'][sample_id]['annopoints']\
                    [0, 0][0, 0]['point'][0]['x'][info_idx][0, 0] + 1
            pose[1, joint_idx, 0] = \
                POS_ANNOTS['annorect'][sample_id]['annopoints']\
                    [0, 0][0, 0]['point'][0]['y'][info_idx][0, 0] + 1
            try:
                pose[2, joint_idx, 0] = \
                    POS_ANNOTS['annorect'][sample_id]['annopoints']\
                        [0, 0][0, 0]['point'][0]['is_visible'][joint_idx][0, 0]
            except IndexError:
                pose[2, joint_idx, 0] = 0
        # Determine the person bounding box.
        visible_joints = np.ma.masked_less(pose, 0)
        x1 = np.min(visible_joints[0, :, 0])
        y1 = np.min(visible_joints[1, :, 0])
        x2 = np.max(visible_joints[0, :, 0])
        y2 = np.max(visible_joints[1, :, 0])
        # Add border.
        border_x = (x2 - x1) // 3
        border_y = (y2 - y1) // 3
        x1 = max(x1 - border_x, 0)
        y1 = max(y1 - border_y, 0)
        x2 = min(x2 + border_x, image.shape[1] - 1)
        y2 = min(y2 + border_y, image.shape[0] - 1)
        visimage = image.copy()
        cv2.rectangle(visimage,
                      (x1, y1), (x2, y2),
                    #   (POS_ANNOTS['annorect'][sample_id]['x1'][0, 0][0, 0],
                    #    POS_ANNOTS['annorect'][sample_id]['y1'][0, 0][0, 0]),
                    #   (POS_ANNOTS['annorect'][sample_id]['x2'][0, 0][0, 0],
                    #    POS_ANNOTS['annorect'][sample_id]['y2'][0, 0][0, 0]),
                      (0, 255, 0),
                      5)
        # Add joints.
        for joint_pos in pose[:, :, 0].transpose((1, 0)):
            if np.all(joint_pos[:2] > 0):
                cv2.circle(visimage,
                           (joint_pos[0],
                            joint_pos[1]),
                           5,
                           (255, 0, 0),
                           5)
        cv2.imwrite(os.path.join(TARGET_DSET_FOLDER, 'with_annotations',
                                 '{0:05d}.png'.format(running_idx)),
                    visimage)
        # Determine the desired scale.
        scale_to_200px = POS_ANNOTS['annorect'][sample_id]['scale'][0, 0][0, 0]
        factor = 1. / scale_to_200px * (300. / 200.)
        extracted_image_os = image[y1:y2, x1:x2, :]
        extracted_image_rs = cv2.resize(extracted_image_os,
                                        (int((x2-x1) * factor),
                                         int((y2-y1) * factor)),
                                        interpolation=cv2.INTER_CUBIC)
        cv2.imwrite(target_name, extracted_image_rs)
        pose[0, :, :] -= x1
        pose[1, :, :] -= y1
        pose[:2, :, :] *= factor
        # Visualize extracted.
        for joint_pos in pose[:, :, 0].transpose((1, 0)):
            if np.all(joint_pos[:2] > 0):
                cv2.circle(extracted_image_rs,
                           (joint_pos[0],
                            joint_pos[1]),
                           5,
                           (255, 0, 0),
                           5)
        cv2.imwrite(os.path.join(TARGET_DSET_FOLDER, 'with_annotations',
                                 '{0:05d}-extracted.png'.format(running_idx)),
                    extracted_image_rs)
        running_idx += 1
        poses.append(pose)
correspondance_file.close()

poses_array = np.dstack(poses)
np.savez_compressed(os.path.join(TARGET_DSET_FOLDER, 'annotations.npz'),
                    poses=poses_array)

#################################################################################
# Testing area.
print(poses_array.shape)
t = np.sum(poses_array, axis=1)
np.argmax(t[2, :])
image = cv2.imread('/is/ps2/classner/caffe/data/mpii-seg/images/00016.jpg')
pose = poses_array[:, :, 15]
for joint_idx, joint_pos in enumerate(pose[:, :].transpose((1, 0))):
    visimage = image.copy()
    cv2.circle(visimage,
               (joint_pos[0],
                joint_pos[1]),
               5,
               (255, 0, 0),
               5)
    cv2.imshow('joint {}'.format(joint_idx), visimage)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
np.savez_compressed(os.path.join(TARGET_DSET_FOLDER, 'annotations-test.npz'),
                    poses=poses_array[:, :, 225:226])
