"""Shared utilities for sync commands"""

import datetime
from hashlib import md5
from json import JSONEncoder

import click


class DateTimeEncoder(JSONEncoder):
    """JSON encoder that handles datetime objects"""

    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        if isinstance(obj, bytes):
            return obj.decode("utf-8", errors="ignore")
        return super().default(obj)


def calc_etag(data, partsize=8388608):
    """Calculate S3 ETag for multipart uploads"""
    if len(data) < partsize:
        return f'"{md5(data).hexdigest()}"'
    md5_digests = []
    for i in range(0, len(data), partsize):
        chunk = data[i : i + partsize]
        md5_digests.append(md5(chunk).digest())
    return md5(b"".join(md5_digests)).hexdigest() + "-" + str(len(md5_digests))


def list_bucket(s3, bucket, prefix=""):
    """List objects in S3 bucket with pagination"""
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


def sum_bucket(s3, bucket, print_every=1000):
    """Summarize bucket contents by directory"""
    d = {}
    for i, (key, size, etag) in enumerate(list_bucket(s3, bucket)):
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


def head(s3, key, bucket):
    """Get object metadata from S3"""
    import botocore.exceptions

    try:
        return s3.head_object(Key=key, Bucket=bucket)
    except botocore.exceptions.ClientError as ce:
        if "404" in str(ce):
            return False


def authenticate_icloud(icloud_username, icloud_password):
    """Authenticate with iCloud and handle 2FA/2SA"""
    from pyicloud import PyiCloudService

    # Prompt for credentials if not provided
    if not icloud_username:
        icloud_username = click.prompt("iCloud Username")
    if not icloud_password:
        icloud_password = click.prompt("iCloud Password", hide_input=True)

    api = PyiCloudService(icloud_username, icloud_password)

    if api.requires_2fa:
        click.echo("Two-factor authentication required.")
        code = click.prompt(
            "Enter the code you received on one of your approved devices"
        )
        result = api.validate_2fa_code(code)
        click.echo(f"Code validation result: {result}")

        if not result:
            click.echo("Failed to verify security code")
            raise click.Abort()

        if not api.is_trusted_session:
            click.echo("Session is not trusted. Requesting trust...")
            result = api.trust_session()
            click.echo(f"Session trust result: {result}")

            if not result:
                click.echo(
                    "Failed to request trust. You will likely be prompted for the code again in the coming weeks"
                )
    elif api.requires_2sa:
        click.echo("Two-step authentication required. Your trusted devices are:")

        devices = api.trusted_devices
        for i, device in enumerate(devices):
            click.echo(
                f"  {i}: {device.get('deviceName', 'SMS to %s' % device.get('phoneNumber'))}"
            )

        device_idx = click.prompt(
            "Which device would you like to use?", type=int, default=0
        )
        device = devices[device_idx]
        if not api.send_verification_code(device):
            click.echo("Failed to send verification code")
            raise click.Abort()

        code = click.prompt("Please enter validation code")
        if not api.validate_verification_code(device, code):
            click.echo("Failed to verify verification code")
            raise click.Abort()

    return api
