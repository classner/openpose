import math
import json

from colormath.color_objects import RGBColor

from django.db import models
from django.core.urlresolvers import reverse

from imagekit.models import ImageSpecField
from imagekit.processors import SmartResize, ResizeToFit
from imagekit.utils import open_image

from common.models import UserBase, ResultBase, EmptyModelBase
from licenses.models import License

from common.utils import compute_label_reward, md5sum, get_content_tuple, \
    get_opensurfaces_storage
from common.geom import normalized, construct_all_uvn_frames, matrix_to_column_list


STORAGE = get_opensurfaces_storage()

class PhotoDataset(EmptyModelBase):
    """ Photo dataset, such as 'LSP', 'BUFFY' """

    #: Scene category name
    name = models.CharField(max_length=127)

    #: Text description of this category
    description = models.TextField(blank=True)

    #: "Parent" category.  Scene categories can be nested in a tree.  Currently none are.
    parent = models.ForeignKey('self', blank=True, null=True)

    def __unicode__(self):
        return self.name

    def name_capitalized(self):
        return self.name[0].upper() + self.name[1:]

    def photo_count(self, **filters):
        qset = self.photos.filter(**Photo.DEFAULT_FILTERS)
        if filters:
            qset = qset.filter(**filters)
        return qset.count()

    class Meta:
        verbose_name = "Photo dataset"
        verbose_name_plural = "Photo datasets"
        ordering = ['name']

class FlickrUser(EmptyModelBase):
    """ Flickr user """

    #: flickr username
    username = models.CharField(max_length=127)

    display_name = models.CharField(max_length=255, blank=True)

    # name shown below the display name
    sub_name = models.CharField(max_length=255, blank=True)

    given_name = models.CharField(max_length=255, blank=True)
    family_name = models.CharField(max_length=255, blank=True)

    # personal website
    website_name = models.CharField(max_length=1023, blank=True)
    website_url = models.URLField(max_length=1023, blank=True)

    #: if true, this user has too many bogus photos and will be ignored
    blacklisted = models.BooleanField(default=False)

    def __unicode__(self):
        return self.username


class Photo(UserBase):
    """
    Photograph
    """

    #: original uploaded image (jpg format)
    image_orig = models.ImageField(upload_to='photos', storage=STORAGE)

    name = models.TextField(blank=True)

    #: Options for thumbnails.
    #: **Warning**: changing this will change the hash on all image thumbnails and you will need to re-resize every photo in the database.
    _THUMB_OPTS = {
        'source': 'image_orig',
        'format': 'JPEG',
        'options': {'quality': 90},
        'cachefile_storage': STORAGE,
    }

    #: The photograph resized to fit inside the rectangle 200 x 400
    image_200 = ImageSpecField([ResizeToFit(200, 2 * 200)], **_THUMB_OPTS)
    #: The photograph resized to fit inside the rectangle 300 x 600
    image_300 = ImageSpecField([ResizeToFit(300, 2 * 300)], **_THUMB_OPTS)

    #: The photograph resized to fit inside the rectangle 512 x 1024
    image_512 = ImageSpecField([ResizeToFit(512, 2 * 512)], **_THUMB_OPTS)
    #: The photograph resized to fit inside the rectangle 1024 x 2048
    image_1024 = ImageSpecField([ResizeToFit(1024, 2 * 1024)], **_THUMB_OPTS)
    #: The photograph resized to fit inside the rectangle 2048 x 4096
    image_2048 = ImageSpecField([ResizeToFit(2048, 2 * 2048)], **_THUMB_OPTS)

    #: The photograph cropped (and resized) to fit inside the square 300 x 300
    image_square_300 = ImageSpecField([SmartResize(300, 300)], **_THUMB_OPTS)

    #: width of ``image_orig``
    orig_width = models.IntegerField(null=True)

    #: height of ``image_orig``
    orig_height = models.IntegerField(null=True)

    #: width/height aspect ratio
    aspect_ratio = models.FloatField(null=True)

    #: optional user description
    description = models.TextField(blank=True)

    #: exif data (output from jhead)
    exif = models.TextField(blank=True)

    #: field of view in degrees of the longer dimension
    fov = models.FloatField(null=True)

    #: focal length in units of height (focal_pixels = height * focal_y)
    focal_y = models.FloatField(null=True)

    #: copyright license
    license = models.ForeignKey(
        License, related_name='photos', null=True, blank=True)

    #: if true, this is synthetic or otherwise manually inserted for special
    #: experiments.
    synthetic = models.BooleanField(default=False)

    #: If True, this photo contains sexual content.
    #: If None, this photo has not been examined for this attribute.
    #: This field is set by admins, not workers, by visually judging the image.
    #: (this is not a limitation; we just didn't think to make this a task
    #: until late in the project)
    inappropriate = models.NullBooleanField()

    #: If True, this photo was NOT taken with a perspective lens (e.g. fisheye).
    #: If None, this photo has not been examined for this attribute.
    #: This field is set by admins, not workers, by visually judging the image.
    #: (this is not a limitation; we just didn't think to make this a task
    #: until late in the project)
    nonperspective = models.NullBooleanField()

    #: Tf True, this photo does not represent what the scene really looks like
    #: from a pinhole camera.  For example, it may have been visibly edited or
    #: is obviously HDR, or has low quality, high noise, excessive blur,
    #: excessive defocus, visible vignetting, long exposure effects, text
    #: overlays, timestamp overlays, black/white borders, washed out colors,
    #: sepia tone or black/white, infrared filter, very distorted tones (note
    #: that whitebalanced is a separate field), or some other effect.
    #:
    #: If None, this photo has not been examined for this attribute.
    #: This field is set by admins, not workers, by visually judging the image.
    #: (this is not a limitation; we just didn't think to make this a task
    #: until late in the project)
    stylized = models.NullBooleanField()

    #: If True, this photo is incorrectly rotated (tilt about the center).
    #: looking up or down does not count as 'rotated'.  This label is
    #: subjective; the image has to be tilted by more than 30 degrees to be
    #: labeled 'rotated'.  The label is mostly intended to capture
    #: images that are clearly 90 degrees from correct.
    #: If None, this photo has not been examined for this attribute.
    #: This field is set by admins, not workers, by visually judging the image.
    #: (this is not a limitation; we just didn't think to make this a task
    #: until late in the project)
    rotated = models.NullBooleanField()

    #: dataset, e.g. "LSP", "BUFFY"
    dataset = models.ForeignKey(
        PhotoDataset, related_name='photos', null=True, blank=True)

    #: flickr user that uploaded this photo
    flickr_user = models.ForeignKey(
        FlickrUser, related_name='photos', null=True, blank=True)

    #: flickr photo id
    flickr_id = models.CharField(max_length=64, null=True, blank=True)

    #: name of photographer or source, if not a Flickr user
    attribution_name = models.CharField(max_length=127, blank=True)
    attribution_url = models.URLField(blank=True)

    #: hash for simple duplicate detection
    md5 = models.CharField(max_length=32)

    class Meta:
        verbose_name = "Photo"
        verbose_name_plural = "Photos"
        ordering = ['aspect_ratio', '-id']

    #: Default filters for views
    DEFAULT_FILTERS = {
        'synthetic': False,
        'inappropriate': False,
        'rotated': False,
        'stylized': False,
        'nonperspective': False,
    }

    def save(self, *args, **kwargs):
        if not self.md5:
            self.md5 = md5sum(self.image_orig)

        if not self.orig_width or not self.orig_height:
            self.orig_width = self.image_orig.width
            self.orig_height = self.image_orig.height

        if not self.aspect_ratio:
            self.aspect_ratio = (float(self.image_orig.width) /
                                 float(self.image_orig.height))

        if not self.focal_y and self.fov:
            dim = max(self.image_orig.width, self.image_orig.height)
            self.focal_y = 0.5 * dim / (self.image_orig.height *
                                        math.tan(math.radians(self.fov / 2)))

        if not self.license and self.flickr_user and self.flickr_id:
            self.license = License.get_for_flickr_photo(
                self.flickr_user, self.flickr_id)

        super(Photo, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.image_orig.url

    def get_absolute_url(self):
        return reverse('photos.views.photo_detail', args=[str(self.id)])

    def get_flickr_url(self):
        if self.flickr_id and self.flickr_user_id:
            return "http://www.flickr.com/photos/%s/%s/" % (
                self.flickr_user.username, self.flickr_id)
        else:
            return None

    def image_height(self, width):
        """ Returns the height of image_<width> """
        return min(2 * width, width / self.aspect_ratio)

    def open_image(self, width='orig'):
        """ Fetch the image at a given size (see the image_<width> fields) """
        cache_attr = '_cache_image_%s' % width
        if hasattr(self, cache_attr):
            return getattr(self, cache_attr)
        pil = open_image(getattr(self, 'image_%s' % width))
        setattr(self, cache_attr, pil)
        return pil

    def get_pixel(self, x, y, width='orig'):
        """ Fetch a pixel, in floating point coordinates (x and y range from
        0.0 inclusive to 1.0 exclusive), at a given resolution (specified by
        width) """
        pil = self.open_image(width=width)
        x = float(x) * pil.size[0]
        y = float(y) * pil.size[1]
        return pil.getpixel((x, y))

    def font_size_512(self):
        """ Helper for svg templates: return the font size that should be used to
        render an image with width 512px, when in an SVG environment that has
        the height scaled to 1.0 units """
        return 10.0 / self.height_512()

    def font_adjustment_512(self):
        """ Helper for svg templates """
        return self.font_size_512() * 0.3

    def height_1024(self):
        """ Helper for templates: return the image height when the width is 1024 """
        return self.image_height(1024)

    def height_512(self):
        """ Helper for templates: return the image height when the width is 512 """
        return self.image_height(512)

    def publishable(self):
        """ True if the license exists and has publishable=True """
        return self.license and self.license.publishable

    def publishable_score(self):
        """ Return a score indicating how 'open' the photo license is """
        if not self.license:
            return 0
        return self.license.publishable_score()

    @staticmethod
    def get_thumb_template():
        return 'photos/thumb.html'

    def get_entry_dict(self):
        """ Return a dictionary of this model containing just the fields needed
        for javascript rendering.  """

        # generating thumbnail URLs is slow, so only generate the ones
        # that will definitely be used.
        return {
            'id': self.id,
            'fov': self.fov,
            'aspect_ratio': self.aspect_ratio,
            'image': {
                #'200': self.image_200.url,
                #'300': self.image_300.url,
                #'512': self.image_512.url,
                '1024': self.image_1024.url,
                '2048': self.image_2048.url,
                'orig': self.image_orig.url,
            }
        }
