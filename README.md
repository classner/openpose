# Openpose

Openpose is a human segmentation tool built on top of OpenSurfaces by Sean Bell
et al. It allows to easily separate foreground and background by using the
GrabCut algorithm. Credits for it's creation go to Martin Kiefel and the
OpenSurfaces authors. It has been used to create the UP dataset(s):
http://up.is.tuebingen.mpg.de. It is heavily based on the OpenSurfaces package (http://opensurfaces.cs.cornell.edu).

## Installing
First, you should decide if you want to run the code only for doing some simple
segmentation tasks or if you are interested in running experiments on Amazon
Mechanical Turk. Installation works on different Linux distributions but scripts
are only provided for Ubuntu (although I did most of the development on a Gentoo
system). For any other distribution please follow the installation scripts that
are called inside the `install_all.sh` script. For running experiments I suggest
using the Docker container; it creates a nice encapsulated unit.

The dependencies include

- django
- rabbitmq
- memcached
- nginx
- various other Python packages.

**Ubuntu**
It is probably best to install into a virtual machine. In there call `bash
scripts/install/install_all.sh` to install all necessary dependencies.

**Docker**
Please use `bash build_docker.sh` to build a [docker](https://www.docker.com/)
image to run the code. It will install all dependencies inside the image. This
takes some time.

## Run
The first thing that we need is a database to store all the information. I have
used two ways to run the database. Locally, for development a postgresql
database ran as part of my development system. In production a postgresl docker
image ran in a separate container from the rest of the project.

### Create Database
Just to mention that somewhere: You can easily backup and restore a postgresql
database with `pg_dump` and `psql`.

**Docker Database**
To start a separate container with a database call `bash scripts/create_db.sh`.
It will setup a container with the name `$PROJECT_NAME-data` so that it can be
found again later by other scripts. The script assumes that the database works
on the local folder `$DB_FOLDER` that was part of the initial configuration.

**Local Database**
A local database be initialized like so

- `mkdir db`
- `sudo chown -R postgres db/`
- `sudo -u postgres initdb db`
- `sudo -u postgres postgres -D db`

### Servers
Once the database is set up we can proceed to the web-app. As mentioned before I
have used two setups for development and production.

**Ubuntu**
This runs a small server for testing purposes. Particularly useful for
debugging. I often extracted live data from the production system and tested it
locally with my test setup.

- `bash scripts/init_db.sh`
- `python scripts/manage.py runserver`

**Docker**
To create a server that is running on port 45001 call `bash
scripts/start_docker.sh`. If you want the image to listen on a different port
please edit the script yourself. Once the image is started you should get access
to a shell. This assumes that you also run the database inside a docker image
with the name $PROJECT_NAME-data! The communication between the two containers
is properly setup by the script.

Once inside the docker container you need to initialize the data with the
presented shell (similar steps are necessary if you restart the container;
without the initialization of the database).

- `cd /home/appuser`
- `bash scripts/init_db.sh`
- `bash scripts/fix_permissions.sh`
- `bash scripts/run.sh`

I always ran the docker container with a bash as interactive container and
detached and attached to the container when I logged on and off the serving
machine. You can detach from a container with `ctrl-p ctrl-q` and for better
handling I usually had a `tmux` running inside the container.

## Add images
Adding images to the database is as easy as calling `python manage.py
import_folder admin test ../data/media/images/`. The script takes the server
user that will own the images (for me this was usually the admin account), the
name of the data-set (here it's `test`) and a folder that contains the JPEG
images (it's the only supported format!).

In case you are using the docker image, the best way to interact with the server
is to copy images and such into the shared folder `media` between the container
and the host machine, which is mounted in `/home/appuser/data/media` inside the
container.

If you want to import pose annotations, run `python manage.py import_mpii_annotation admin test annotations.npz` followed by
`python manage.py create_part_task admin test`.

Otherwise:
The above action only adds images. You need to specify the area that contains
the object/person with `python manage.py create_bounding_box admin test`. Again
`admin` is the user that create the objects and `test` is the data-set's name.
We could supply a person's annotation to the bounding box. Please add your own
code, if you want to do that. You might want to have a look at the examples in
the `pose/cmd` folder. Nevertheless, you can safely proceed without adding any
other information.

After that we need to create a segmentation task: `python manage.py
create_task admin test`. This script scans through all bounding box annotations
of the `test` data-set and will add a task for those bounding boxes that do not
own one.

At
[http://localhost:45001/segmentation/mask](http://localhost:45001/segmentation/mask)
you should now be able to see the segmentation tasks and submit them once you
are satisfied. The web interface is only accessible to logged in users that you
can create through the web-page's admin panel. You can find the panel in the
upper right corner of the index page once you logged in as admin.

The quality of the segmentations can be checked on
[http://localhost:45001/segmentation/quality](http://localhost:45001/segmentation/quality).
This presents you all submitted tasks that do not have a quality assessment,
yet. We used this to curate the submissions from the Turkers.

## Caching

The server uses two methods for caching: the services `memcached` and
`supervisor`. Both must be restarted to see effects of changes.

## Get the segmentation data
You can use the following script to extract the segmentation information. The
script expects the data-set's name, a file that contains the names to the images
and output folder: `python manage.py extract_segmentation test <(echo
'image-slider-2') output-folder`. The image names are derived from the original
file name of the JPEG image without its extension.

## Aftermath
Once you are happy with everything, do not forget to change the debug state in
`server/config/settings_local.py` to `False`.
