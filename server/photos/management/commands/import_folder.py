import os
from optparse import make_option

from clint.textui import progress

from django.core.management.base import BaseCommand
from accounts.models import UserProfile

from photos.models import PhotoDataset, FlickrUser
from photos.add import add_photo
#from licenses.models import License


class Command(BaseCommand):
    args = '<user> <datasetname> <dir>'
    help = 'Adds photos from folder'

    option_list = BaseCommand.option_list + (
        make_option(
            '--delete',
            action='store_true',
            dest='delete',
            default=False,
            help='Delete photos after they are visited'),
    )

    def handle(self, *args, **options):
        if len(args) != 3:
            print 'Please supply a folder and the name of the dataset.'
            return

        username = args[0]
        dataset_name = args[1]
        folder = args[2]

        delete = bool(options['delete'])

        user = UserProfile.objects.get(user__username=username)

        print 'Visiting: %s' % folder
        for root, dirs, files in os.walk(folder):
            print 'Visiting %s: %d files' % (root, len(files))

            # only create a category if has at least one photo
            dataset, _ = PhotoDataset.objects.get_or_create(name=dataset_name)

            num_added = 0
            for filename in progress.bar(files):
                if filename.endswith(".jpg"):
                    path = os.path.join(root, filename)

                    flickr_username = None
                    flickr_id = None
                    flickr_user = None
                    name, _ = os.path.splitext(os.path.basename(filename))

                    #license = License.objects.get_or_create(
                        #user=admin_user, name='CC BY-NC-SA 2.0')[0]

                    try:
                        add_photo(
                            path=path,
                            user=user,
                            dataset=dataset,
                            flickr_user=flickr_user,
                            flickr_id=flickr_id,
                            #license=license,
                            must_have_exif=False,
                            must_have_fov=False,
                            exif='',
                            synthetic=False,
                            inappropriate=False,
                            rotated=False,
                            stylized=False,
                            nonperspective=False,
                            name=name,
                        )
                    except Exception as e:
                        print '\nNot adding photo:', e
                    else:
                        print '\nAdded photo:', path
                        num_added += 1

                    if delete:
                        from common.tasks import os_remove_file
                        os_remove_file.delay(path)

            print 'Added %d photos to %s' % (num_added, root)
