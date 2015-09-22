# OpenSurfaces

OpenSurfaces is a large database of annotated surfaces created from real-world
consumer photographs. Our annotation framework draws on crowdsourcing to
segment surfaces from photos, and then annotate them with rich surface
properties, including material, texture and contextual information.

Documentation is available at: http://opensurfaces.cs.cornell.edu/docs/

## Citation

If you use our code, please cite our paper:

    Sean Bell, Paul Upchurch, Noah Snavely, Kavita Bala
    OpenSurfaces: A Richly Annotated Catalog of Surface Appearance
    ACM Transactions on Graphics (SIGGRAPH 2013)

    @article{bell13opensurfaces,
		author = "Sean Bell and Paul Upchurch and Noah Snavely and Kavita Bala",
		title = "Open{S}urfaces: A Richly Annotated Catalog of Surface Appearance",
		journal = "ACM Trans. on Graphics (SIGGRAPH)",
		volume = "32",
		number = "4",
		year = "2013",
	}

and if you use the Intrinsic Images code, please also cite:

    Sean Bell, Kavita Bala, Noah Snavely
    Intrinsic Images in the Wild
    ACM Transactions on Graphics (SIGGRAPH 2014)

    @article{bell14intrinsic,
		author = "Sean Bell and Kavita Bala and Noah Snavely",
		title = "Intrinsic Images in the Wild",
		journal = "ACM Trans. on Graphics (SIGGRAPH)",
		volume = "33",
		number = "4",
		year = "2014",
	}

It's nice to see how many people are using our code; please "star" this project
on GitHub and report any bugs using the
[issue tracker](https://github.com/seanbell/opensurfaces/issues).

## Configure
Init your configuration.
`python scripts/create_config.py`

## Installing
First, you should decide if you want to run the code only for doing some simple
segmentation tasks or if you are interested in running experiments on Amazon
Mechanical Turk. Installation works on different Linux distributions but scripts
are only provided for Ubuntu. For any other distribution please follow the
installation scripts that are called inside the `install_all.sh` script.

**Ubuntu**
It is probably best to install into a virtual machine. In there call `bash
scripts/install/install_all.sh` to install all necessary dependencies.

**Docker**
Please use `bash build_docker.sh` to build a [docker](https://www.docker.com/)
image to run the code. It will install all dependencies inside the image. This
takes some time.

## Run

### Create Database
**Docker Database**
- `bash scripts/create_db.sh`

**Local Database**
- `mkdir db`
- `sudo chown -R postgres db/`
- `sudo -u postgres initdb db`
- `sudo -u postgres postgres -D db`

### Servers
**Docker**
To create a server that is running on port 45001 call `bash
scripts/start_docker.sh`. If you want the image to listen on a different port
please edit the script yourself. This assumes that you also run the database
inside a docker image!

Once inside the docker container you need to initialize the data
- `cd /home/appuser`
- `bash scripts/init_db.sh`

**Ubuntu**
`bash scripts/init_db.sh`
`bash scripts/fix_permissions.sh`
`bash scripts/run.sh`

## Add images
Adding images to the database is as easy as calling `python manage.py
import_folder admin test ../data/media/images/`. Plug-in the user name that owns
the images!

In case you are using the docker image, the best way to interact with the server
is to copy images and such into the shared folder `media`, which is mounted in
`/home/appuser/data/media` inside the container.

The above action only adds images. You need to specify the area that contains
the object/person with `python manage.py create_bounding_box admin test`. Again
`admin` is the user that create the objects and `test` is the data-set's name.
We could supply a person's annotation to the bounding box. Please add your own
code, if you want to do that. You might want to have a look at the examples in
the `pose/cmd` folder.

After that we need to create a segmentation task. Use `python manage.py
create_task admin test`.

At
[http://localhost:45001/segmentation/mask](http://localhost:45001/segmentation/mask)
you should now be able to see the segmentation tasks.

The quality of the segmentations can be checked on
[http://localhost:45001/segmentation/quality](http://localhost:45001/segmentation/quality).

## Get the segmentation data
You can use the following script to extract the segmentation information. The
script expects the data-set's name, a file that contains the names to the images
that should be extracted and and output folder: `python manage.py
extract_segmentation test <(echo 'image-slider-2') output-folder`.

## Aftermath
Once you are happy with everything, do not forget to change the debug state in
`server/config/settings_local.py` to `False`.

