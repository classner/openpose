from decimal import Decimal
from django.conf import settings

from common.utils import has_foreign_key

from segmentation.models import PersonSegmentation

from pose.models import Person

def configure_experiments():
    """ This function is automatically called by
    the command ./manage.py mtconfigure """

    # must be imported locally to avoid a circular import
    from mturk.utils import configure_experiment

    # aliases
    sandbox = settings.MTURK_SANDBOX
    production = not sandbox

    configure_experiment(
        slug='segment_person',
        variant='"person_fix"',
        template_dir='segmentation/experiments',
        module='segmentation.experiments',
        version=2,  # 2: intrinsic images, 1: original opensurfaces
        reward=Decimal('0.11'),
        num_outputs_max=1,
        contents_per_hit=2,
        content_type_model=Person,
        out_content_type_model=PersonSegmentation,
        out_content_attr='person',
        content_filter={
            'segmentations__isnull': True,
            },
        title='Carefully segment a person',
        description='Given an image, your job is to segment a person from an image.',
        keywords='person,images,segment',
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


def external_task_extra_context(slug, context):
    """ Add extra context for each task (called by
    ``mturk.views.external.external_task_GET``) """

    if slug == 'quality_segmentation':
        context['html_yes'] = 'segmentation aligned with central person'
        context['html_no'] = 'bad segmentation'
