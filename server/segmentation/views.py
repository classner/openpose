import json
import base64
from random import sample
from cStringIO import StringIO

from PIL import Image

import numpy as np

from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

from common.utils import json_success_response, json_error_response, \
        html_error_response, dict_union

from accounts.models import UserProfile

from mturk.views.external import external_task_browser_check
from mturk.models import Experiment

from pose.models import ParsePose

from segmentation.utils import calc_person_overlay_img
from segmentation.models import PersonSegmentation, \
        PersonSegmentationQuality, PersonSegmentationTask
from segmentation.experiments import external_task_extra_context

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

        ids = results.keys()

        user, _ = UserProfile.objects.get_or_create(user=request.user)

        PersonSegmentationQuality.mturk_submit(user,
                PersonSegmentation.objects.filter(id__in=ids), results,
                time_ms, time_active_ms, data[u'version'])

        return json_success_response()
    else:
        segmentations_filter = {
                'qualities': None,
                }

        if dataset_id != 'all':
            dataset_id = int(dataset_id)

            segmentations_filter = dict_union(segmentations_filter, {
                'task__person__photo__dataset_id': dataset_id
                })

        segmentations = PersonSegmentation.objects.filter(**segmentations_filter)

        if segmentations:
            # pick a random non annotated picture
            #contents = [segmentations[np.random.randint(len(segmentations))]]
            contents = sample(segmentations, min(50, segmentations.count()))

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
            }

            external_task_extra_context('segment_quality', context)

            return render(request, u'segmentation/experiments/quality_segmentation.html', context)
        else:
            return html_error_response(request,
                    'All segmentations are marked.')

@login_required()
@ensure_csrf_cookie
def task_segment(request, dataset_id='all', part=None):
    # replace this with a fetch from your database
    if request.method == 'POST':
        data = request.REQUEST
        if not (u'results' in data):
            return json_error_response(u'No results')

        results = json.loads(data[u'results'])
        time_ms = json.loads(data[u'time_ms'])
        time_active_ms = json.loads(data[u'time_active_ms'])

        ids = results.keys()

        user = UserProfile.objects.get(user=request.user)

        PersonSegmentation.mturk_submit(user,
                PersonSegmentationTask.objects.filter(id__in=ids),
                results, time_ms, time_active_ms, data[u'version'])

        return json_success_response()
    else:
        response = external_task_browser_check(request)
        if response:
            return response

        task_filter = {
                'responses__isnull': True
                }

        if dataset_id != 'all':
            dataset_id = int(dataset_id)

            task_filter = dict_union(task_filter, {
                'person__photo__dataset_id': dataset_id
                })

        if part:
            task_filter = dict_union(task_filter, {
                'part': part
                })

        tasks = (PersonSegmentationTask.objects.filter(**task_filter))
                #.exclude(responses__qualities__isnull = True)
                #.exclude(responses__qualities__correct = True))

        if tasks:
            # pick a random non annotated picture
            contents = sample(tasks, min(1, tasks.count()))

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
    for id_, annotations in results.items():
        scribbles = annotations.get(u'scribbles', [])
        part = annotations.get(u'part', None)

        task = PersonSegmentationTask.objects.get(id=id_)

        overlay_img = calc_person_overlay_img(task, scribbles)
        overlay_img.save(bytes_io, u'PNG')

        return HttpResponse(
                base64.standard_b64encode(bytes_io.getvalue()),
                content_type=u'data/text')


