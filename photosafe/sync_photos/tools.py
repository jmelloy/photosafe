from json import JSONEncoder
import datetime
from hashlib import md5
import boto3
import botocore.exceptions

s3 = boto3.client("s3", "us-west-2")


# subclass JSONEncoder
class DateTimeEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()


def calc_etag(data, partsize=8388608):
    if len(data) < partsize:
        return f'"{md5(data).hexdigest()}"'
    md5_digests = []
    for i in range(0, len(data), partsize):
        chunk = data[i:i + partsize]
        md5_digests.append(md5(chunk).digest())
    return md5(b''.join(md5_digests)).hexdigest() + '-' + str(len(md5_digests))


def list_bucket(bucket, prefix=""):
    key = ""
    rs = {"IsTruncated": True}
    total = 0
    while rs["IsTruncated"]:
        rs = s3.list_objects(Bucket=bucket, Prefix=prefix, Marker=key)
        if not rs.get("Contents"):
            return

        for row in rs.get("Contents", []):
            yield row["Key"], row.get("Size", 0), row["ETag"]
        else:
            key = row["Key"]
            total += len(rs.get("Contents", []))
    print("%d rows returned for s3://%s/%s" % (total, bucket, prefix))

def sum_bucket(bucket, print_every=1000):
    d = {}
    for i, (key, size, etag) in enumerate(list_bucket(bucket)):
        directory_name = "/".join(key.split("/")[0:-1]) + "/" if "/" in key else ""
        (sz, items) = d.get(directory_name, (0, 0))
        sz += size
        items += 1
        d[directory_name] = (sz, items)

        if i % print_every == 0:
            print(" --", i, directory_name, d[directory_name])

    for k, v in sorted(d.items(), key=lambda x: x[1][0], reverse=True):
        print(f"{k:15} {v[1]:,} {v[0] / 1024 ** 3:.3}")

    return d

def head(key, bucket='jmelloy-photo-backup'):
    try:
        return s3.head_object(Key=key, Bucket=bucket)
    except botocore.exceptions.ClientError as ce:
        if "404" in str(ce):
            return False
        raise
