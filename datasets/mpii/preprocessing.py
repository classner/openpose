"""Do the preprocessing for the MPII datset."""
# pylint: disable=C0103

import scipy.io

MAT = scipy.io.loadmat('/home/christoph/Downloads/mpii_human_pose_v1_u12_1/'
                       'mpii_human_pose_v1_u12_1.mat')

print(type(MAT['RELEASE'][0, 0]['annolist'][0, 0]))
print(MAT['RELEASE'][0, 0]['act'][:, 0].shape)

ACTS = MAT['RELEASE'][0, 0]['act'][:, 0]
print(ACTS[:100])

activities = {}
actnames = []
for act_idx, act in enumerate(ACTS):
    if act[2][0, 0] == -1:
        continue
    act_idn = act[2][0, 0]  # act[0][0] + act[1][0]
    # if act[2][0, 0] not in activities:
    if act_idn not in activities:
        print('New activity detected: {}.'.format(act_idn))
#        activities[act[2][0, 0]] = {'name': act[0][0],
#                                    'occurences': []}
        activities[act_idn] = []
        actnames.append(act[1][0])
    # activities[act[2][0, 0]]['occurences'].append(act_idx)
    activities[act_idn].append(act_idx)

print(len(activities))
print(activities.keys())

for actkey, actval in activities.items():
    print(len(actval['occurences']))
