import numpy as np

from pose.models import AABB

from PIL import Image, ImageDraw

from imagekit.utils import open_image

#from multilabel import segment
from cv2 import grabCut, GC_INIT_WITH_RECT, GC_INIT_WITH_MASK

def calc_person_overlay_img(task, scribbles):
    parse_pose = task.parse_pose
    bounding_box = task.person.bounding_box

    # check if the person already has a segmentation that we can use to improve
    # the quality
    segmentation = None
    if task.part:
        tasks = task.person.segmentation_tasks.filter(
                responses__qualities__correct=True, part__isnull=True)
        if tasks:
            response = tasks[0].responses.filter(qualities__correct=True)[0]
            segmentation = open_image(response.segmentation)
        else:
            print('no task')

        # add other segmenations if they are correct

    return calc_pose_overlay_img(task.person.photo, scribbles,
            parse_pose=parse_pose, part=task.part, bounding_box=bounding_box,
            segmentation=segmentation)

def calc_pose_overlay_img(photo, scribbles, parse_pose=None, part=None,
        bounding_box=None, segmentation=None):
    img = photo.open_image()

    # get the annotation
    if parse_pose:
        annotation_scribbles = build_annotation_scribbles(parse_pose, part,
                photo.aspect_ratio)
    else:
        annotation_scribbles = []

    return calc_overlay_img(img, bounding_box, annotation_scribbles,
            scribbles, segmentation)

def build_annotation_scribbles(parse_pose, part, aspect_ratio):
    all_end_points, all_visibility = parse_pose.visible_part_end_points()
    end_points, visibility = parse_pose.visible_part_end_points(part)

    background_annotation_scribbles = [
            {'points': all_end_points[2*s : 2*s+2, :],
                'is_foreground': False}
            for s in xrange(all_end_points.shape[0] // 2)
            if all_visibility[2*s] and all_visibility[2*s + 1]
            ]

    foreground_annotation_scribbles = [
            {'points': end_points[2*s : 2*s+2, :],
                'is_foreground': True}
            for s in xrange(end_points.shape[0] // 2)
            if visibility[2*s] and visibility[2*s + 1]
            ]

    return background_annotation_scribbles + foreground_annotation_scribbles

def calc_overlay_img(imgImage, bounding_box, maybe_scribbles, scribbles, segmentationImage):
    img = np.asarray(imgImage)

    #bounding_box = None

    if bounding_box:
        scaled_bounding_box = np.round(np.array([
            bounding_box.min_point[0],
            bounding_box.min_point[1],
            bounding_box.max_point[0],
            bounding_box.max_point[1]])
            * img.shape[0]).astype(np.int)

        img = img[scaled_bounding_box[1]:scaled_bounding_box[3],
                scaled_bounding_box[0]:scaled_bounding_box[2], :]
    else:
        bounding_box = AABB(np.array([0, 0]),
                np.array([float(img.shape[1]) / img.shape[0], 1]))

    height, width = img.shape[0], img.shape[1]

    scale = height

    bgd_model = np.zeros((1, 65), np.float64)
    fgd_model = np.zeros((1, 65), np.float64)

    margin = 1
    foreground_scribble_label = 1
    background_scribble_label = 0
    foreground_prob_label = 3
    background_prob_label = 2

    rect = (margin, margin, width-margin, height-margin)

    scribbles_map = np.zeros(img.shape[:2], dtype=np.uint8)

    grabCut(img, scribbles_map, rect, bgd_model, fgd_model, 5, GC_INIT_WITH_RECT)

    scribbles_map_img = Image.fromarray(scribbles_map)
    draw = ImageDraw.Draw(scribbles_map_img)

    # strage: this should have been done by the frame, but somehow there is a
    # tendency to lean right. I have no good explanation for that
    scribble_margin = 0
    draw.line((
        scribble_margin,
        scribble_margin,
        width-scribble_margin-1,
        scribble_margin),
        fill=background_scribble_label,
        width=scribble_margin * 2 + 1)
    draw.line((
        width-scribble_margin-1,
        scribble_margin, width-scribble_margin-1,
        height-scribble_margin-1),
        fill=background_scribble_label,
        width=scribble_margin * 2 + 1)
    draw.line((width-scribble_margin-1,
        height-scribble_margin-1,
        scribble_margin,
        height-scribble_margin-1),
        fill=background_scribble_label,
        width=scribble_margin * 2 + 1)
    draw.line((scribble_margin,
        height-scribble_margin-1,
        scribble_margin,
        scribble_margin),
        fill=background_scribble_label,
        width=scribble_margin * 2 + 1)

    for scribble in maybe_scribbles:
        points = np.array(scribble[u'points'])

        if scribble[u'is_foreground']:
            fill = foreground_scribble_label
        else:
            fill = background_prob_label

        for s in range(1, points.shape[0]):
            draw.line((
                (points[s-1, 0] - bounding_box.min_point[0]) * width
                / bounding_box.width,
                (points[s-1, 1] - bounding_box.min_point[1]) * height
                / bounding_box.height,
                (points[s, 0] - bounding_box.min_point[0]) * width
                / bounding_box.width,
                (points[s, 1] - bounding_box.min_point[1]) * height
                / bounding_box.height,
                ),
                fill=fill, width=1)

    for scribble in scribbles:
        points = np.array(scribble[u'points'])

        if scribble[u'is_foreground']:
            fill = foreground_scribble_label
        else:
            fill = background_scribble_label

        for s in range(1, points.shape[0]):
            draw.line((
                (points[s-1, 0] - bounding_box.min_point[0]) * width
                / bounding_box.width,
                (points[s-1, 1] - bounding_box.min_point[1]) * height
                / bounding_box.height,
                (points[s, 0] - bounding_box.min_point[0]) * width
                / bounding_box.width,
                (points[s, 1] - bounding_box.min_point[1]) * height
                / bounding_box.height,
                ),
                fill=fill, width=1)

    scribbles_map = np.asarray(scribbles_map_img).copy()

    if segmentationImage:
        segmentation = np.asanyarray(segmentationImage)
        scribbles_map[segmentation == 0] = background_scribble_label
    else:
        print('NO segmentation')

    grabCut(img, scribbles_map, rect, bgd_model, fgd_model, 5, GC_INIT_WITH_MASK)

    seg = np.where((scribbles_map==1) + (scribbles_map==3),255,0).astype('uint8')

    return Image.fromarray(seg)
