import re
import lmdb

db = lmdb.open('/home/mkiefel/fuse/cluster/projects/caffe/experiments_iccv2015/lsp/person_segmentation.train.lmdb', map_size=int(1e12))

m = re.compile('im\d+$')

valid = True

with db.begin(write=True) as txn:
    with txn.cursor() as cursor:
        valid = cursor.first()
        while valid:
            k = cursor.key()
            if not m.search(k):
                print(k)
                valid = cursor.delete()
                # valid = cursor.next()
            else:
                valid = cursor.next()
