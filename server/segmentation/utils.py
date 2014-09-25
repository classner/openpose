import numpy as np

from PIL import Image, ImageDraw

#from multilabel import segment
from cv2 import grabCut, GC_INIT_WITH_RECT, GC_INIT_WITH_MASK

def calc_pose_overlay_img(photo, scribbles):
    img = photo.open_image()

    # get the annotation
    try:
        # just grab the first annotation
        pose = photo.parse_pose.all()[0]

        annotation_scribbles = build_annotation_scribbles(pose)
    except IndexError:
        annotation_scribbles = []

    return calc_overlay_img(img, annotation_scribbles + scribbles)

def build_annotation_scribbles(parse_pose):
    end_points = parse_pose.end_points()

    foreground_annotation_scribbles = [
            {'points': end_points[2*s : 2*s+2, :],
                'is_foreground': True}
            for s in xrange(end_points.shape[0] // 2)
            ]

    # draw a frame, we are sure that this will be background
    background_annotation_scribbles = [
            {'points': np.array([[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]),
                'is_foreground': False}
            ]

    return background_annotation_scribbles + foreground_annotation_scribbles

def calc_overlay_img(imgImage, scribbles):
    width, height = imgImage.size

    img = np.asarray(imgImage)

    scale = max(width, height)

    bgd_model = np.zeros((1, 65), np.float64)
    fgd_model = np.zeros((1, 65), np.float64)

    rect = (5, 5, width-5, height-5)

    scribbles_map = np.zeros(img.shape[:2], dtype=np.uint8)
    grabCut(img, scribbles_map, rect, bgd_model, fgd_model, 5, GC_INIT_WITH_RECT)

    scribbles_map_img = Image.fromarray(scribbles_map)
    draw = ImageDraw.Draw(scribbles_map_img)

    for scribble in scribbles:
        points = np.array(scribble[u'points'])

        if scribble[u'is_foreground']:
            fill = 1
        else:
            fill = 0

        for s in range(1, points.shape[0]):
            draw.line((points[s-1, 0] * scale, points[s-1, 1] * scale,
                    points[s, 0] * scale, points[s, 1] * scale),
                    fill=fill, width=2)

    scribbles_map = np.asarray(scribbles_map_img)

    grabCut(img, scribbles_map, rect, bgd_model, fgd_model, 5, GC_INIT_WITH_MASK)

    seg = np.where((scribbles_map==1) + (scribbles_map==3),255,0).astype('uint8')

    Image.fromarray(seg).save('out.png')

    return Image.fromarray(seg)
