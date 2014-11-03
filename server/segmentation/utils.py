import numpy as np

from pose.models import AABB

from PIL import Image, ImageDraw

#from multilabel import segment
from cv2 import grabCut, GC_INIT_WITH_RECT, GC_INIT_WITH_MASK

def calc_person_overlay_img(task, scribbles):
    parse_pose = task.parse_pose
    bounding_box = task.person.bounding_box

    return calc_pose_overlay_img(task.person.photo, scribbles,
            parse_pose=parse_pose, part=task.part, bounding_box=bounding_box)

def calc_pose_overlay_img(photo, scribbles, parse_pose=None, part=None,
        bounding_box=None):
    img = photo.open_image()

    # get the annotation
    if parse_pose:
        annotation_scribbles = build_annotation_scribbles(parse_pose, part,
                photo.aspect_ratio)
    else:
        annotation_scribbles = []

    return calc_overlay_img(img, bounding_box, annotation_scribbles + scribbles)

def build_annotation_scribbles(parse_pose, part, aspect_ratio):
    end_points, visibility = parse_pose.visible_part_end_points(part)

    foreground_annotation_scribbles = [
            {'points': end_points[2*s : 2*s+2, :],
                'is_foreground': True}
            for s in xrange(end_points.shape[0] // 2)
            if visibility[2*s] and visibility[2*s + 1]
            ]

    return foreground_annotation_scribbles

def calc_overlay_img(imgImage, bounding_box, scribbles):
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
    forground_scribble_label = 1
    background_scribble_label = 0
    forground_prediction_label = 1
    background_prediction_label = 0

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

    for scribble in scribbles:
        points = np.array(scribble[u'points'])

        if scribble[u'is_foreground']:
            fill = forground_scribble_label
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

    scribbles_map = np.asarray(scribbles_map_img)

    grabCut(img, scribbles_map, rect, bgd_model, fgd_model, 5, GC_INIT_WITH_MASK)

    seg = np.where((scribbles_map==1) + (scribbles_map==3),255,0).astype('uint8')

    Image.fromarray(seg).save('out.png')

    return Image.fromarray(seg)
