import json
from cStringIO import StringIO
import base64
from tempfile import NamedTemporaryFile

from PIL import Image

from django.db import models, transaction
from django.core.files.images import ImageFile

from common.models import EmptyModelBase, ResultBase
from common.utils import get_content_tuple, recursive_sum, \
        get_opensurfaces_storage

from pose.models import ParsePose, Person

from segmentation.utils import calc_person_overlay_img

STORAGE = get_opensurfaces_storage()

class PersonSegmentationTask(EmptyModelBase):
    """ A segmentation task. """

    person = models.ForeignKey(Person, related_name='segmentation_tasks')

    parse_pose = models.ForeignKey(ParsePose,
            related_name='segmentation_tasks', blank=True, null=True)

    part = models.CharField(
            max_length=2, choices=map(
                lambda (k, p): (k, p.description),
                ParsePose.part_description.iteritems()),
            null=True, blank=True)

    def get_entry_dict(self, include_scribbles=False):
        """ Return a dictionary of this model containing just the fields needed
        for javascript rendering.  """

        # generating thumbnail URLs is slow, so only generate the ones
        # that will definitely be used.
        if self.person.bounding_box_data:
            bounding_box = json.loads(self.person.bounding_box_data)
        else:
            bounding_box = None

        # if there is already a segmentation we take the newest one and add the
        # scribbles here
        scribbles = None
        responses = self.responses.all().order_by('-added')
        if include_scribbles and responses:
            scribbles = json.loads(responses[0].scribbles)

        parts = []

        if self.parse_pose:
            parse_pose, visible = self.parse_pose.visible_part_end_points(self.part)
            parts = [ p
                      for i, p in enumerate(parse_pose.tolist())
                      if visible[i]
            ]

        part_name = None
        if self.part:
            part_name = ParsePose.part_description[self.part].description

        return {
                u'id': self.id,
                u'bounding_box': bounding_box,
                u'parse_pose': parts,
                u'scribbles': scribbles,
                u'part_name': part_name,
                u'photo': {
                    u'fov': self.person.photo.fov,
                    u'aspect_ratio': self.person.photo.aspect_ratio,
                    u'image': {
                        #'200': self.photo.image_200.url,
                        #'300': self.photo.image_300.url,
                        #'512': self.photo.image_512.url,
                        #'1024': self.photo.image_1024.url,
                        #'2048': self.photo.image_2048.url,
                        u'orig': self.person.photo.image_orig.url,
                        }
                    }
                }

class PersonSegmentation(ResultBase):
    """ Person segmentation submitted by user. """

    task = models.ForeignKey(PersonSegmentationTask, related_name='responses')

    segmentation = models.ImageField(upload_to='segmentation', storage=STORAGE)

    # Vertices format: x1,y1,x2,y2,x3,y3,... (coords are fractions of width/height)
    # (this format allows easy embedding into javascript)
    scribbles = models.TextField(null=True)
    # num_vertices should be equal to len(points.split(','))//2
    num_scribbles = models.IntegerField(null=True)

    def __unicode__(self):
        return ('%s scribbles in segmentation for part %s' %
                (self.num_scribbles, self.task.part))

    def get_thumb_template(self):
        return 'segmentation/segmentation_thumb.html'

    def scribbles_svg_path(self):
        """ Returns submitted scribbles as SVG path """
        scribbles = json.loads(self.scribbles)

        data = [[], []]
        for scribble in scribbles:
            if scribble[u'is_foreground']:
                set_index = 0
            else:
                set_index = 1

            for i,point in enumerate(scribble[u'points']):
                if i == 0:
                    data[set_index].append(u'M %f %f ' % (point[0], point[1]))
                else:
                    data[set_index].append(u'L %f %f ' % (point[0], point[1]))

        return {u'foreground': ''.join(data[0]), u'background': ''.join(data[1])}

    @staticmethod
    def mturk_submit(user, hit_contents, results, time_ms, time_active_ms,
                     version, mturk_assignment=None, **kwargs):
        """ Add new instances from a mturk HIT after the user clicks [submit] """

        if unicode(version) != u'2.0':
            raise ValueError("Unknown version: %s" % version)

        new_objects = {}
        for task in hit_contents:
            task_id = str(task.id)
            scribbles = results[task_id][u'scribbles']
            person_time_ms = time_ms[task_id]
            person_time_active_ms = time_active_ms[task_id]

            # check if the scribbles make sense
            for scribble in scribbles:
                for point in scribble[u'points']:
                    if len(point) != 2:
                        raise ValueError("Point with more than 2 coordinates")

            # check if the results contain a segmentation already, if so do not
            # recalculate the segmentation

            overlay_img = None
            if u'segmentation' in results[task_id]:
                try:
                    overlay_img_data = base64.standard_b64decode(
                            results[task_id][u'segmentation'])
                    overlay_img = Image.open(StringIO(overlay_img_data))
                    print("reusing segmentation data")
                except:
                    overlay_img = None

            if not overlay_img:
                # generate the segmentation image
                overlay_img = calc_person_overlay_img(task, scribbles)
                print("NOT reusing segmentation data")

            with transaction.atomic():
                with NamedTemporaryFile(prefix=u'segmentation_' +
                        task.person.photo.name + u'_', suffix=u'.png') as f:
                    overlay_img.save(f, u"PNG")
                    f.seek(0)
                    segmentation = ImageFile(f)

                    new_obj, created = task.responses.get_or_create(
                        user=user,
                        segmentation=segmentation,
                        mturk_assignment=mturk_assignment,
                        time_ms=person_time_ms,
                        time_active_ms=person_time_active_ms,
                        # (repr gives more float digits)
                        scribbles=json.dumps(scribbles),
                        num_scribbles=len(scribbles),
                    )

                    if created:
                        new_objects[get_content_tuple(task)] = [new_obj]

        return new_objects

class PersonSegmentationQuality(ResultBase):
    segmentation = models.ForeignKey(PersonSegmentation, related_name='qualities')
    correct = models.BooleanField(default=False)
    canttell = models.NullBooleanField()

    def __unicode__(self):
        if self.canttell:
            return "can't tell"
        else:
            return 'correct' if self.correct else 'not correct'

    class Meta:
        verbose_name = "Segmentation quality vote"
        verbose_name_plural = "Segmentation quality votes"

    @staticmethod
    def mturk_submit(user, hit_contents, results, time_ms, time_active_ms,
            version, mturk_assignment=None, **kwargs):
        """ Add new instances from a mturk HIT after the user clicks [submit] """

        if unicode(version) != u'1.0':
            raise ValueError("Unknown version: '%s'" % version)
        if not hit_contents:
            return {}

        # best we can do is average
        avg_time_ms = time_ms / len(hit_contents)
        avg_time_active_ms = time_active_ms / len(hit_contents)

        new_objects = {}
        for shape in hit_contents:
            selected = (
                str(results[unicode(shape.id)]['selected']).lower() == 'true')
            canttell = (
                str(results[unicode(shape.id)]['canttell']).lower() == 'true')

            new_obj, created = shape.qualities.get_or_create(
                user=user,
                mturk_assignment=mturk_assignment,
                time_ms=avg_time_ms,
                time_active_ms=avg_time_active_ms,
                correct=selected,
                canttell=canttell,
            )

            if created:
                new_objects[get_content_tuple(shape)] = [new_obj]

        return new_objects
