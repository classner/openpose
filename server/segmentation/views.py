import json

from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse

from PIL import Image

import numpy as np

import base64

from cStringIO import StringIO

from segmentation.utils import calc_pose_overlay_img

from photos.models import Photo
from segmentation.models import PersonSegmentation
from pose.models import ParsePose
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
        scribbles = annotations.get(u'scribbles', [])

        overlay_img = calc_pose_overlay_img(Photo.objects.get(id=img_id), scribbles)

        overlay_img.save(bytes_io, u"JPEG")

        return HttpResponse(
                base64.standard_b64encode(bytes_io.getvalue()),
                content_type=u'data/text')


