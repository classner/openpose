import random
import string
import sys
import os.path

from django.core.management.base import BaseCommand

from clint.textui import progress

import numpy as np

from PIL import Image

import lmdb


class Command(BaseCommand):
    help = 'Add images without segmentation to a training database'

    def random_key_(self):
        return ''.join(
            random.choice(string.ascii_uppercase + string.digits)
            for _ in range(6))

    def write_segmentation_(self, caffe, image_path, txn):
        # Only take the part of the image that contains the person.
        image = np.array(Image.open(image_path), dtype=np.uint8)

        # This image is assumed not to have any person in it.
        segmentation = np.zeros((image.shape[0], image.shape[1], 1),
                                dtype=np.uint8)

        input = np.transpose(
            np.concatenate((image, segmentation),
                           axis=2),
            [2, 0, 1])

        datum = caffe.io.array_to_datum(input)
        photo_name = os.path.splitext(
            os.path.basename(image_path))[0]
        txn.put(self.random_key_() + str(photo_name),
                datum.SerializeToString(),
                overwrite=False)

    def handle(self, *args, **options):
        caffe_root = args[0]
        include_list_path = args[1]
        db_path = args[2]

        # Load caffe
        sys.path.insert(0, os.path.join(caffe_root, 'python'))
        import caffe

        # Get LMDB file database up and running
        db = lmdb.open(db_path, map_size=int(1e12))
        txn = db.begin(write=True)
        transactions = 0

        with open(include_list_path, 'r') as list_file:
            for image_path in progress.bar(list_file.readlines()):
                image_path = image_path.rstrip()

                self.write_segmentation_(caffe, image_path, txn)

                transactions += 1

                if transactions > 300:
                    txn.commit()
                    transactions = 0
                    txn = db.begin(write=True)

        if transactions > 0:
            txn.commit()

        db.close()
