import os
import math
import json
import shutil
import tempfile
import subprocess
import numpy as np
from celery import shared_task
from PIL import Image, ImageDraw

from imagekit.utils import open_image, save_image
from pilkit.utils import extension_to_format
from pilkit.processors import ResizeToFit

from django.db.models import Sum, Q

from photos.models import FlickrUser, Photo
from licenses.models import License
from common.geom import homo_line, unit_to_sphere, sphere_to_unit, normalized_cross, abs_dot
from common.utils import progress_bar
from common.http import download
from pyquery import PyQuery as pq


@shared_task
def update_photo_license(photo_id):
    p = Photo.objects.get(id=photo_id)
    p.license = License.get_for_flickr_photo(p.flickr_user, p.flickr_id)
    p.save()


@shared_task
def update_flickr_users(ids, show_progress=False):
    """ Scrape Flickr for information about Flickr User profiles.

    :param ids: list of database ids (not Flick usernames)
    """

    values = FlickrUser.objects \
        .filter(id__in=ids) \
        .values_list('id', 'username')

    if show_progress:
        values = progress_bar(values)

    for (id, username) in values:
        html = download('https://www.flickr.com/people/%s/' % username)
        if not html:
            continue

        d = pq(html)

        profile = d('div.profile-section')
        given_name = profile('span.given-name').text().strip()
        family_name = profile('span.family-name').text().strip()
        website_name = profile('a.url').text().strip()
        website_url = profile('a.url').attr('href')
        if website_url:
            website_url = website_url.strip()
        else:
            website_url = ""

        person = d('div.person')
        display_name = person('span.character-name-holder').text().strip()
        sub_name = person('h2').text().strip()

        FlickrUser.objects.filter(id=id).update(
            display_name=display_name,
            sub_name=sub_name,
            given_name=given_name,
            family_name=family_name,
            website_name=website_name,
            website_url=website_url,
        )

        if show_progress:
            print '%s: display: "%s" (%s), name: "%s" "%s", web: "%s" (%s)' % (
                username, display_name, sub_name, given_name, family_name,
                website_name, website_url)

@shared_task
def download_photo_task(photo_id, filename, format=None, larger_dimension=None):
    """ Downloads a photo and stores it, potentially downsampling it and
    potentially converting formats """

    parent_dir = os.path.dirname(filename)
    if not os.path.exists(parent_dir):
        os.makedirs(parent_dir)

    photo = Photo.objects.get(id=photo_id)
    if not larger_dimension and not format:
        photo.image_orig.seek(0)
        with open(filename, 'wb') as f:
            shutil.copyfileobj(photo.image_orig, f)
    else:
        if larger_dimension <= 512:
            image = open_image(photo.image_512)
        elif larger_dimension <= 1024:
            image = open_image(photo.image_1024)
        elif larger_dimension <= 2048:
            image = open_image(photo.image_2048)
        else:
            image = open_image(photo.image_orig)

        if max(image.size) > larger_dimension:
            if image.size[0] > image.size[1]:
                image = image.resize((
                    larger_dimension,
                    larger_dimension * image.size[1] / image.size[0]), Image.ANTIALIAS)
            else:
                image = image.resize((
                    larger_dimension * image.size[0] / image.size[1],
                    larger_dimension), Image.ANTIALIAS)

        if not format:
            format = extension_to_format(os.path.splitext(filename).lower())

        image.save(filename, format)


