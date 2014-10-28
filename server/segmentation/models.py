from django.db import models, transaction
from django.core.files.images import ImageFile

import json

from cStringIO import StringIO

import base64

from tempfile import NamedTemporaryFile

from pose.models import Person
from common.models import EmptyModelBase, ResultBase

from common.utils import get_content_tuple, recursive_sum, \
        get_opensurfaces_storage

from segmentation.utils import calc_person_overlay_img

from PIL import Image

STORAGE = get_opensurfaces_storage()

class PersonSegmentation(ResultBase):
    """ Person segmentation submitted by user. """

    person = models.ForeignKey(Person, related_name='segmentations')

    segmentation = models.ImageField(upload_to='segmentation', storage=STORAGE)

    # Vertices format: x1,y1,x2,y2,x3,y3,... (coords are fractions of width/height)
    # (this format allows easy embedding into javascript)
    scribbles = models.TextField(null=True)
    # num_vertices should be equal to len(points.split(','))//2
    num_scribbles = models.IntegerField(null=True)

    def __unicode__(self):
        return '%s scribbles in segmentation' % self.num_scribbles

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
        for person in hit_contents:
            person_id = str(person.id)
            scribbles = results[person_id][u'scribbles']
            person_time_ms = time_ms[person_id]
            person_time_active_ms = time_active_ms[person_id]

            # check if the scribbles make sense
            for scribble in scribbles:
                for point in scribble[u'points']:
                    if len(point) != 2:
                        raise ValueError("Point with more than 2 coordinates")

            # check if the results contain a segmentation already, if so do not
            # recalculate the segmentation

            overlay_img = None
            if u'segmentation' in results[person_id]:
                try:
                    overlay_img_data = base64.standard_b64decode(
                            results[person_id][u'segmentation'])
                    overlay_img = Image.open(StringIO(overlay_img_data))
                    print "reusing segmentation data"
                except:
                    overlay_img = None

            if not overlay_img:
                # generate the segmentation image
                overlay_img = calc_person_overlay_img(person, scribbles)
                print "NOT reusing segmentation data"

            with transaction.atomic():
                with NamedTemporaryFile(prefix=u'segmentation_' +
                        person.photo.name + u'_', suffix=u'.png') as f:
                    overlay_img.save(f, u"PNG")
                    f.seek(0)
                    segmentation = ImageFile(f)

                    new_obj, created = person.segmentations.get_or_create(
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
                        new_objects[get_content_tuple(person)] = [new_obj]

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
