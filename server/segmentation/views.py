#from multilabel import segment

import json

from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse

from PIL import Image, ImageDraw

import numpy as np

import base64

from StringIO import StringIO

from photos.models import Photo
from segmentation.models import PersonSegmentation
from mturk.views.external import external_task_browser_check
from mturk.models import Experiment
from accounts.models import UserProfile
from common.utils import json_success_response, json_error_response

@ensure_csrf_cookie
@staff_member_required
def task(request):
    # replace this with a fetch from your database
    if request.method == 'POST':
        data = request.REQUEST
        if not (u'results' in data):
            return json_error_response(u'No results')

        results = json.loads(data[u'results'])
        time_ms = json.loads(data[u'time_ms'])
        time_active_ms = json.loads(data[u'time_active_ms'])

        assert(len(results) == 1)

        # for not really needed here...
        img_id = results.keys()[0]

        experiment, _ = Experiment.objects.get_or_create(slug=u'segment_person',
                variant=u'')

        user, _ = UserProfile.objects.get_or_create(user=request.user)

        PersonSegmentation.mturk_submit(user,
                Photo.objects.filter(id=img_id), results, time_ms,
                time_active_ms, experiment, u'1.0')

        return json_success_response()
    else:
        response = external_task_browser_check(request)
        if response:
            return response

        img = Photo.objects.filter(scribbles=None)[0]

        # hard-coded example image:
        context = {
            # the current task
            u'content': img,

            # if 'true', ask the user a feedback survey at the end and promise
            # payment to complete it.  Must be 'true' or 'false'.
            u'ask_for_feedback': 'false',

            # feedback_bonus is the payment in dollars that we promise users
            # for completing feedback
            u'feedback_bonus': 0.02,

            # template containing html for instructions
            u'instructions': 'segmentation/experiments/segment_person_inst_content.html'
        }

    return render(request, u'segmentation/experiments/segment_person.html', context)

@ensure_csrf_cookie
def segmentation(request):
    """
    Call the interactive segmentation method to serve a new mask.
    """

    bytes_io = StringIO()
    data = request.REQUEST

    if not ('results' in data):
        return json_error_response('No results')

    try:
        results = json.loads(data[u'results'])
    except ValueError:
        return json_error_response(u'JSON parse error')

    # for not really needed here...
    for img_id, annotations in results.items():
        scribbles_coords = annotations.get(u'scribbles', [])

        scribbles = [
                mangle_scribble(scribble_coords)
                for scribble_coords in scribbles_coords
                ]

        img = Photo.objects.filter(id=img_id)[0].open_image()
        overlay_img = Image.fromarray(calc_overlay_img(img, scribbles))

        overlay_img.save(bytes_io, u"JPEG")

        return HttpResponse(
                base64.standard_b64encode(bytes_io.getvalue()),
                content_type=u'data/text')

def mangle_scribble(scribble_coords):
    #if not (('points' in scribble_coords) and ('is_foreground' in
        #scribble_coords)) or (len(scribble_coords['points']) % 2) != 0:
        #return {'points': np.array((0, 2)), 'is_foreground': True}

    return {'points': np.array(scribble_coords['points']).reshape((-1, 2)),
            'is_foreground': scribble_coords['is_foreground']
            }

def calc_overlay_img(img, scribbles):
    width, height = img.size
    scribbles_map = Image.fromarray(np.ones((height, width), dtype=np.uint8) * 255)
    draw = ImageDraw.Draw(scribbles_map)

    for scribble in scribbles:
        points = scribble['points']

        if scribble['is_foreground']:
            fill = 1
        else:
            fill = 0

        for s in range(1, points.shape[0]):
            draw.line((points[s-1, 0] * width, points[s-1, 1] * height,
                    points[s, 0] * width, points[s, 1] * height),
                    fill=fill, width=2)
    #seg = segment(np.asfortranarray(img), np.asarray(scribbles_map, order='fortran'))
    seg = np.ones_like(img)

    seg[seg == 1] = 255

    return seg