"""Do the preprocessing for the MPII dataset."""
# pylint: disable=C0103, E1101

from __future__ import print_function

import os
import csv
import numpy as np
import scipy.io
import cv2


DSET_FOLDER = '/is/ps2/classner/caffe/data/mpii/'
MAT = scipy.io.loadmat(os.path.join(DSET_FOLDER,
                                    'mpii_human_pose_v1_u12.mat'))
ANNOLIST = scipy.io.loadmat(os.path.join(DSET_FOLDER,
                                         'annolist_dataset_v12.mat'))
TARGET_DSET_FOLDER = '/is/ps2/classner/caffe/data/mpii-seg-test/'

print(type(MAT['RELEASE'][0, 0]['annolist'][0, 0]))
print(MAT['RELEASE'][0, 0]['act'][:, 0].shape)

ACTS = MAT['RELEASE'][0, 0]['act'][:, 0]
TRAIN_TEST = MAT['RELEASE'][0, 0]['img_train'][0]
POS_ANNOTS = MAT['RELEASE'][0, 0]['annolist'][0]
TPOS_ANNOTS = ANNOLIST['annolist'][0]
SINGLE_ANNOTS = MAT['RELEASE'][0, 0]['single_person']

np.sum(MAT['RELEASE'][0, 0]['img_train'][0] == 0)
np.sum(np.array([val[0].size == 1 for val in MAT['RELEASE'][0, 0]['single_person']]))
a = np.array([val[0].size == 1 for val in MAT['RELEASE'][0, 0]['single_person']])
np.sum(np.logical_and(MAT['RELEASE'][0, 0]['img_train'][0] == 0, a))
# Get some statistics.
# Total person annotations in the test set.
TOTAL_PERSONS = 0
for rect in POS_ANNOTS['annorect']:
    TOTAL_PERSONS += rect.shape[1]
print("Total person annotations in the test set: {}.".format(TOTAL_PERSONS))
SEP_PERSONS = 0
for single_annot in SINGLE_ANNOTS:
    SEP_PERSONS += single_annot[0].shape[0]
print("Separate person annotations in the test set: {}.".format(SEP_PERSONS))
print("Images in the test set: {}.".format(np.sum(TRAIN_TEST == 0)))

# The internal structure of the activity storage is
#
# * category name: act[0][0]
# * activity name: act[1][0]
# * activity id: act[2][0, 0]
#
# Multiple activity ids get merged together to one activity. In the training
# set, there are 397 activities, the rest is only present in the test set.
activities = {}
im_poses = {}
actnames = []
for act_idx, act in enumerate(ACTS):
    if act[2][0, 0] == -1:
        act_idn = 'unknown-in-test'
    else:
        act_idn = act[1][0]  # act[0][0] + act[1][0]
    if act_idn not in activities:
        print('New activity detected: {}.'.format(act_idn))
        activities[act_idn] = []
        if act[2][0, 0] == -1:
            actnames.append(act_idn)
        else:
            actnames.append(act[1][0])
    if TRAIN_TEST[act_idx] == 0:
        if SINGLE_ANNOTS[act_idx][0].size == 1:
            if os.path.exists(os.path.join(DSET_FOLDER, 'images',
                                           POS_ANNOTS[act_idx][0][0, 0][0][0])):
                foundpose = False
                # for idx in range(TPOS_ANNOTS['annorect'][act_idx]['annopoints'].shape[1]):
                idx = SINGLE_ANNOTS[act_idx][0][0, 0] - 1
                # try:
                # Check whether pose annotation is availabe.
                _ = TPOS_ANNOTS['annorect'][act_idx]['annopoints']\
                    [0, idx][0, 0]['point'][0]['x']
                _ = TPOS_ANNOTS['annorect'][act_idx]['annopoints']\
                    [0, idx][0, 0]['point'][0]['y']
                if not act_idx in im_poses.keys():
                    im_poses[act_idx] = []
                im_poses[act_idx].append(idx)
                if not foundpose:
                    foundpose = True
                activities[act_idn].append(act_idx)
                # except ValueError:
                #     pass
                # except IndexError:
                #     pass
                if not foundpose:
                    print("Missing pose!")
            else:
                print("Missing image: {}!".format(
                    POS_ANNOTS[act_idx][0][0, 0][0][0]))

print(len(activities))
print(os.linesep.join(activities.keys()))

for actkey, actval in activities.items():
    print(actkey, len(actval))

selected_activities = []
for act_name in activities.keys():
    if len(activities[act_name]) > 0:
        selected_activities.append(act_name)

print('Number of selected activities:', len(selected_activities))
for key, val in im_poses.items():
    assert len(val) == 1

# Sample 3 images from each.
np.random.seed(42)
sampled_ids = {}
for act_name in selected_activities:
    sampled_ids[act_name] = activities[act_name][:]
    # np.random.permutation(activities[act_name])[:5]

# Copy these images to a folder with restricted structure for easier handling.
correspondance_file = open(os.path.join(TARGET_DSET_FOLDER,
                                        'correspondances.csv'), 'w')
correspondance_csv = csv.writer(correspondance_file)
correspondance_csv.writerow(['mpii_id',
                             'mpii_name',
                             'image_name',
                             'bb_up_left_x_0b_inc',
                             'bb_up_left_y_0b_inc',
                             'bb_low_left_x_0b_exc',
                             'bb_low_left_y_0b_exc'])
poses = []
running_idx = 1
for act_name in sampled_ids.keys():
    for sample_id in sampled_ids[act_name]:
        for pose_idx in im_poses[sample_id]:
            image_name = os.path.join(DSET_FOLDER, 'images',
                                      POS_ANNOTS[sample_id][0][0, 0][0][0])
            target_name = os.path.join(TARGET_DSET_FOLDER, 'images',
                                       '{0:05d}.jpg'.format(running_idx))
            image = cv2.imread(image_name)
            pose = np.ones((3, 16, 1), dtype='int') * -1
            for info_idx in range(TPOS_ANNOTS['annorect'][sample_id]['annopoints']\
                                    [0, pose_idx][0, 0]['point'][0].shape[0]):
                joint_idx = TPOS_ANNOTS['annorect'][sample_id]['annopoints']\
                                [0, pose_idx][0, 0]['point'][0]['id'][info_idx][0, 0]
                pose[0, joint_idx, 0] = \
                    TPOS_ANNOTS['annorect'][sample_id]['annopoints']\
                        [0, pose_idx][0, 0]['point'][0]['x'][info_idx][0, 0] - 1
                pose[1, joint_idx, 0] = \
                    TPOS_ANNOTS['annorect'][sample_id]['annopoints']\
                        [0, pose_idx][0, 0]['point'][0]['y'][info_idx][0, 0] - 1
                try:
                    pose[2, joint_idx, 0] = \
                        TPOS_ANNOTS['annorect'][sample_id]['annopoints']\
                            [0, pose_idx][0, 0]['point'][0]['is_visible'][joint_idx][0, 0]
                except IndexError:
                    pose[2, joint_idx, 0] = 0
            # Determine the person bounding box.
            visible_joints = np.ma.masked_less(pose, 0)
            x1 = np.min(visible_joints[0, :, 0])
            y1 = np.min(visible_joints[1, :, 0])
            x2 = np.max(visible_joints[0, :, 0])
            y2 = np.max(visible_joints[1, :, 0])
            # Get the scale.
            scale_to_200px = TPOS_ANNOTS['annorect'][sample_id]['scale'][0, pose_idx][0, 0]
            # Add border.
            if (x2 - x1) > (y2 - y1):
                # landscape format.
                border_x = (x2 - x1) / 4.
                border_y = (y2 - y1) / 2.
            else:
                border_x = (x2 - x1) / 2.
                border_y = (y2 - y1) / 4.
            x1 = max(x1 - border_x, 0)
            y1 = max(y1 - border_y, 0)
            x2 = min(x2 + border_x, image.shape[1] - 1)
            y2 = min(y2 + border_y, image.shape[0] - 1)
            # Fix extreme cases.
            if float(x2 - x1) / float(y2 - y1) < 0.3:
                # Raise the width.
                x1 = max(x1 - 2 * border_x, 0)
                x2 = min(x2 + 2 * border_x, image.shape[1] - 1)
            elif float(y2 - y1) / float(x2 - x1) < 0.3:
                # Raise the height.
                y1 = max(y1 - 2 * border_y, 0)
                y2 = min(y2 + 2 * border_y, image.shape[0] - 1)
            x1, x2, y1, y2 = int(x1), int(x2), int(y1), int(y2)
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
            factor = 1. / scale_to_200px * (300. / 200.)
            extracted_image_os = image[y1:y2, x1:x2, :]
            correspondance_csv.writerow([sample_id,
                                         POS_ANNOTS[sample_id][0][0, 0][0][0],
                                         '{0:05d}.jpg'.format(running_idx),
                                         x1, y1, x2, y2])
            correspondance_file.flush()
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

################################################################################
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
