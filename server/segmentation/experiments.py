from decimal import Decimal

from django.conf import settings

from common.utils import has_foreign_key

from pose.models import Person

from segmentation.models import PersonSegmentationTask, PersonSegmentation

def configure_experiments():
    """ This function is automatically called by
    the command ./manage.py mtconfigure """

    # must be imported locally to avoid a circular import
    from mturk.utils import configure_experiment

    # aliases
    sandbox = settings.MTURK_SANDBOX
    production = not sandbox

    # full person annotation
    configure_experiment(
        slug='segment_person',
        variant='"person_fix"',
        template_dir='segmentation/experiments',
        module='segmentation.experiments',
        version=2,  # 2: intrinsic images, 1: original opensurfaces
        reward=Decimal('0.14'),
        num_outputs_max=1,
        contents_per_hit=2,
        content_type_model=PersonSegmentationTask,
        out_content_type_model=PersonSegmentation,
        out_content_attr='task',
        content_filter={
            'responses__isnull': True,
            'part__isnull': True,
            },
        title='Carefully segment a person',
        description='Given an image, your job is to segment a person from an image.',
        keywords='person,images,segment',
        #frame_height=8000,
        requirements={},
        auto_add_hits=True,
        has_tutorial=True,
    )

    # part annotation
    configure_experiment(
        slug='segment_part_person',
        variant='',
        template_dir='segmentation/experiments',
        module='segmentation.experiments',
        version=2,  # 2: intrinsic images, 1: original opensurfaces
        reward=Decimal('0.11'),
        num_outputs_max=1,
        contents_per_hit=3,
        content_type_model=PersonSegmentationTask,
        out_content_type_model=PersonSegmentation,
        out_content_attr='task',
        content_filter={
            # only take tasks where we want to segment a part
            'part__isnull': False,
            },
        title='Carefully segment a part of a person',
        description='Given an image, your job is to segment a part of a person '
            + 'from an image.',
        keywords='person,part,images,segment',
        #frame_height=8000,
        requirements={},
        auto_add_hits=True,
        has_tutorial=True,
    )

def update_votes_cubam(show_progress=False):
    """ This function is automatically called by
    mturk.tasks.mturk_update_votes_cubam_task """

    from mturk.cubam import update_votes_cubam
    changed_objects = []

    return changed_objects


def update_changed_objects(changed_objects):
    """ This function is automatically called by
    mturk.tasks.mturk_update_votes_cubam_task
    with all objects that were changed by new votes.  """

    pass

def content_priority(experiment, obj):
    if experiment.slug == 'segment_quality':
        return 1
    elif experiment.slug == 'segment_person':
        return 1
    elif experiment.slug == 'segment_part_person':
        task = obj
        photo = task.person.photo

        dataset = photo.dataset
        if dataset.name == 'LSP':
            photo_number = int(photo.name[2:])

            return 30000 + photo_number
        else:
            return 10000 + photo.id

def external_task_extra_context(slug, context):
    """ Add extra context for each task (called by
    ``mturk.views.external.external_task_GET``) """

    if slug == 'segment_quality':
        context[u'html_yes'] = 'segmentation aligned with central person'
        context[u'html_no'] = 'bad segmentation'
