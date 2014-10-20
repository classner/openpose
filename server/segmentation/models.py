from django.db import models, transaction
from django.core.files.images import ImageFile

import json

from tempfile import NamedTemporaryFile

from photos.models import Photo
from common.models import EmptyModelBase, ResultBase

from common.utils import get_content_tuple, recursive_sum, \
        get_opensurfaces_storage

from segmentation.utils import calc_pose_overlay_img

STORAGE = get_opensurfaces_storage()

class PersonSegmentation(ResultBase):
    """ Person segmentation submitted by user. """

    photo = models.ForeignKey(Photo, related_name='scribbles')

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

    def publishable(self):
        return self.photo.publishable()

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
        for photo in hit_contents:
            scribbles = results[str(photo.id)][u'scribbles']
            time_ms_list = time_ms[str(photo.id)][u'scribbles']
            time_active_ms_list = time_active_ms[str(photo.id)][u'scribbles']

            if len(scribbles) != len(time_ms_list):
                raise ValueError("Result length mismatch (%s scribbles, %s times)" % (
                    len(scribbles), len(time_ms_list)))

            # check if the scribbles make sense
            for scribble in scribbles:
                for point in scribble[u'points']:
                    if len(point) != 2:
                        raise ValueError("Point with more than 2 coordinates")

            # generate the segmentation image
            overlay_img = calc_pose_overlay_img(photo, scribbles)
            with transaction.atomic():
                with NamedTemporaryFile(prefix=u'segmentation_' + photo.name + u'_', suffix=u'.png') as f:
                    overlay_img.save(f, u"PNG")
                    f.seek(0)
                    segmentation = ImageFile(f)

                    new_obj, created = photo.scribbles.get_or_create(
                        user=user,
                        segmentation=segmentation,
                        mturk_assignment=mturk_assignment,
                        time_ms=recursive_sum(time_ms),
                        time_active_ms=recursive_sum(time_active_ms),
                        # (repr gives more float digits)
                        scribbles=json.dumps(scribbles),
                        num_scribbles=len(scribbles),
                    )

                    if created:
                        new_objects[get_content_tuple(photo)] = [new_obj]

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
