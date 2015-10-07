"""Part annotation related task."""
# pylint: disable=F0401, R0201, R0903
from clint.textui import progress, puts, colored

from django.core.management.base import BaseCommand
from accounts.models import UserProfile

from pose.models import Person


class Command(BaseCommand):  # pylint: disable=W0232

    """Command implementation."""

    args = '<user> <dataset> [<part>]'
    help = ('Create segmentation tasks. If part is not given a full '
            'segmentation is created.')

    def handle(self, *args, **options):  # pylint: disable=W0613
        """Implementation."""
        dataset_name = args[1]
        if len(args) < 2:
            puts(colored.red('Please supply a dataset name and optionally a '
                             'part name.'))
            return
        else:
            username = args[0]
            dataset_name = args[1]
            part = None

            if len(args) > 2:
                part = args[2]
            elif len(args) > 3:
                puts(colored.red('Too many arguments.'))
                return

        # user = UserProfile.objects.get(user__username=username)
        persons = Person.objects.filter(photo__dataset__name=dataset_name)

        created_count = 0
        for person in progress.bar(persons):
            # check if this person has a proper segmentation
            correct_full_tasks = person.segmentation_tasks.filter(
                part__isnull=True,
                responses__qualities__correct=True).count()

            if correct_full_tasks > 0 or part is None:
                # check if there is not already a part task that we would like
                # to create
                _, created = person.segmentation_tasks.get_or_create(
                    # user=user,
                    parse_pose=person.parse_poses.all()[0],
                    part=part)

                if created:
                    created_count += 1

        puts('created {} new tasks'.format(created_count))
