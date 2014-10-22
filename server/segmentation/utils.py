import numpy as np

from PIL import Image, ImageDraw

#from multilabel import segment
from cv2 import grabCut, GC_INIT_WITH_RECT, GC_INIT_WITH_MASK

def calc_pose_overlay_img(photo, scribbles, parse_pose=None, bounding_box=None):
    img = photo.open_image()

    # get the annotation
    if parse_pose:
        annotation_scribbles = build_annotation_scribbles(parse_pose,
                photo.aspect_ratio)
    else:
        annotation_scribbles = []

    return calc_overlay_img(img, bounding_box, annotation_scribbles + scribbles)

def build_annotation_scribbles(parse_pose, aspect_ratio):
    end_points = parse_pose.end_points()

    foreground_annotation_scribbles = [
            {'points': end_points[2*s : 2*s+2, :],
                'is_foreground': True}
            for s in xrange(end_points.shape[0] // 2)
            ]

    # draw a frame, we are sure that this will be background
    background_annotation_scribbles = [
            {'points': np.array([[0, 0], [0, 1], [aspect_ratio, 1],
                [aspect_ratio, 0], [0, 0]]),
                'is_foreground': False}
            ]

    return background_annotation_scribbles + foreground_annotation_scribbles

def calc_overlay_img(imgImage, bounding_box, scribbles):
    img = np.asarray(imgImage)

    #bounding_box = None

    if bounding_box:
        scaled_bounding_box = np.round(np.array(bounding_box) *
                img.shape[0]).astype(np.int)

        img = img[scaled_bounding_box[1]:scaled_bounding_box[3],
                scaled_bounding_box[0]:scaled_bounding_box[2], :]

        offset = scaled_bounding_box[0:2]
    else:
        offset = np.zeros((2))


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
    # tendency to lean right. I have not good explanation for that
    margin = 0
    draw.line((margin, margin, width-margin-1, margin),
            fill=background_scribble_label, width=margin * 2 + 1)
    draw.line((width-margin-1, margin, width-margin-1, height-margin-1),
            fill=background_scribble_label, width=margin * 2 + 1)
    draw.line((width-margin-1, height-margin-1, margin, height-margin-1),
            fill=background_scribble_label, width=margin * 2 + 1)
    draw.line((margin, height-margin-1, margin, margin),
            fill=background_scribble_label, width=margin * 2 + 1)

    for scribble in scribbles:
        points = np.array(scribble[u'points'])

        if scribble[u'is_foreground']:
            fill = forground_scribble_label
        else:
            fill = background_scribble_label

        for s in range(1, points.shape[0]):
            draw.line((points[s-1, 0] * scale - offset[0],
                points[s-1, 1] * scale - offset[1],
                points[s, 0] * scale - offset[0],
                points[s, 1] * scale - offset[1]),
                    fill=fill, width=1)

    scribbles_map = np.asarray(scribbles_map_img)

    grabCut(img, scribbles_map, rect, bgd_model, fgd_model, 5, GC_INIT_WITH_MASK)

    seg = np.where((scribbles_map==1) + (scribbles_map==3),255,0).astype('uint8')

    Image.fromarray(seg).save('out.png')

    return Image.fromarray(seg)
