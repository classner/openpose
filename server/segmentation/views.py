import json

from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

from PIL import Image

import numpy as np

import base64

from random import sample

from cStringIO import StringIO

from segmentation.utils import calc_person_overlay_img

from segmentation.models import PersonSegmentation, \
        PersonSegmentationQuality
from pose.models import Person, ParsePose
from mturk.views.external import external_task_browser_check
from mturk.models import Experiment
from accounts.models import UserProfile
from common.utils import json_success_response, json_error_response, \
        html_error_response, dict_union

@login_required
@ensure_csrf_cookie
def task_quality(request, dataset_id='all'):
    # replace this with a fetch from your database
    if request.method == 'POST':
        data = request.REQUEST
        if not (u'results' in data):
            return json_error_response(u'No results')

        results = json.loads(data[u'results'])
        time_ms = json.loads(data[u'time_ms'])
        time_active_ms = json.loads(data[u'time_active_ms'])

        photo_ids = results.keys()

        user, _ = UserProfile.objects.get_or_create(user=request.user)

        PersonSegmentationQuality.mturk_submit(user,
                PersonSegmentation.objects.filter(id__in=photo_ids), results,
                time_ms, time_active_ms, data[u'version'])

        return json_success_response()
    else:
        segmentations_filter = {
                'qualities': None,
                }

        if dataset_id != 'all':
            dataset_id = int(dataset_id)

            segmentations_filter = dict_union(segmentations_filter, {
                'photo__dataset_id': dataset_id
                })

        segmentations = PersonSegmentation.objects.filter(**segmentations_filter)

        if segmentations:
            # pick a random non annotated picture
            #contents = [segmentations[np.random.randint(len(segmentations))]]
            contents = sample(segmentations, 10)

            context = {
                # the current task
                u'contents_json': json.dumps(
                    [c.get_entry_dict() for c in contents]),
                u'content_id_json': json.dumps(
                    [{'id': c.id} for c in contents]),
                u'contents': contents,

                # if 'true', ask the user a feedback survey at the end and promise
                # payment to complete it.  Must be 'true' or 'false'.
                u'ask_for_feedback': 'false',

                # feedback_bonus is the payment in dollars that we promise users
                # for completing feedback
                u'feedback_bonus': 0.0,

                # template containing html for instructions
                u'instructions': 'segmentation/experiments/quality_segmentation_inst_content.html',

                u'content_thumb_template': 'segmentation/experiments/quality_segmentation_thumb.html',

                u'html_yes': 'segmentation aligned with central person',
                u'html_no': 'bad segmentation',
            }

            return render(request, u'segmentation/experiments/quality_segmentation.html', context)
        else:
            return html_error_response(request,
                    'All segmentations are marked.')

@login_required()
@ensure_csrf_cookie
def task_segment(request, dataset_id='all'):
    # replace this with a fetch from your database
    if request.method == 'POST':
        data = request.REQUEST
        if not (u'results' in data):
            return json_error_response(u'No results')

        results = json.loads(data[u'results'])
        time_ms = json.loads(data[u'time_ms'])
        time_active_ms = json.loads(data[u'time_active_ms'])

        segmentation_ids = results.keys()

        user = UserProfile.objects.get(user=request.user)

        PersonSegmentation.mturk_submit(user,
                Person.objects.filter(id__in=segmentation_ids),
                results, time_ms, time_active_ms, data[u'version'])

        return json_success_response()
    else:
        response = external_task_browser_check(request)
        if response:
            return response

        person_filter = {
                }

        if dataset_id != 'all':
            dataset_id = int(dataset_id)

            person_filter = dict_union(photo_filter, {
                'photo__dataset_id': dataset_id
                })

        persons = (Person.objects.filter(**person_filter)
                .exclude(segmentations__qualities__isnull = True)
                .exclude(segmentations__qualities__correct = True))

        if persons:
            # pick a random non annotated picture
            contents = [persons[np.random.randint(len(persons))]]
            #contents = [persons[0]]

            context = {
                # the current task
                u'contents_json': json.dumps(
                    [c.get_entry_dict() for c in contents]),
                u'content_id_json': json.dumps(
                    [{'id': c.id} for c in contents]),
                u'contents': contents,

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
        else:
            return html_error_response(request,
                    'All images are already segmented.')

@ensure_csrf_cookie
def segmentation(request):
    """
    Call the interactive segmentation method to serve a new mask.
    """

    bytes_io = StringIO()
    data = request.REQUEST

    results = json.loads(data[u'results'])

    if unicode(data[u'version']) != u'2.0':
        raise ValueError("Unknown version: %s" % version)

    # for not really needed here...
    for person_id, annotations in results.items():
        scribbles = annotations.get(u'scribbles', [])

        person = Person.objects.get(id=person_id)

        overlay_img = calc_person_overlay_img(person, scribbles)
        overlay_img.save(bytes_io, u'PNG')

        return HttpResponse(
                base64.standard_b64encode(bytes_io.getvalue()),
                content_type=u'data/text')


