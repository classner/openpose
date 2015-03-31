import sys
import os.path

from django.core.management.base import BaseCommand

import numpy as np

import lmdb


class Command(BaseCommand):
    help = 'Compute database mean'

    def handle(self, *args, **options):
        caffe_root = args[0]
        db_path = args[1]

        # Load caffe
        sys.path.insert(0, os.path.join(caffe_root, 'python'))
        from caffe.proto import caffe_pb2
        import caffe

        # Get LMDB file database up and running.
        db = lmdb.open(db_path, map_size=int(1e12))

        # A mean for every color channel.
        mean = np.zeros((3))
        count = 0

        with db.begin() as txn:
            with txn.cursor() as cursor:
                for k, raw in iter(cursor):
                    datum = caffe_pb2.Datum()
                    datum.ParseFromString(raw)

                    input = caffe.io.datum_to_array(datum)
                    size = input.shape[1] * input.shape[2]
                    weight_mean = count / float(count + size)
                    weight_update = 1.0 / float(count + size)
                    mean = (mean * weight_mean +
                            input.sum(axis=2).sum(axis=1)[:-1] * weight_update)

                    count += size

        print(mean)
        db.close()
