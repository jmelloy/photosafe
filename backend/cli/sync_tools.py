"""Shared utilities for sync commands"""

import datetime
import time
from hashlib import md5
from json import JSONEncoder
from pathlib import PosixPath


import click
import requests


class PhotoSafeAuth:
    """Handle authentication and automatic reauthentication for PhotoSafe API"""

    def __init__(self, base_url, username, password, max_retries=3, initial_wait=1):
        """Initialize auth handler

        Args:
            base_url: Base URL for the PhotoSafe API
            username: API username
            password: API password
            max_retries: Maximum number of retry attempts for server errors
            initial_wait: Initial wait time in seconds (doubles with each retry)
        """
        self.base_url = base_url
        self.username = username
        self.password = password
        self.max_retries = max_retries
        self.initial_wait = initial_wait
        self.token = None
        self.user = None

        # Authenticate on initialization
        self._authenticate()

    def _authenticate(self):
        """Authenticate with the API and store the token"""
        try:
            r = requests.post(
                f"{self.base_url}/api/auth/login",
                data={"username": self.username, "password": self.password},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            r.raise_for_status()
            self.token = r.json()["access_token"]

            # Get user info
            r = requests.get(
                f"{self.base_url}/api/auth/me",
                headers={"Authorization": f"Bearer {self.token}"},
            )
            r.raise_for_status()
            self.user = r.json()

            click.echo(f"Authenticated as {self.user.get('username')}")
        except requests.exceptions.RequestException as e:
            click.echo(f"Authentication failed: {e}", err=True)
            raise

    def request(self, method, url, **kwargs):
        """Make an authenticated request with automatic retry and reauthentication

        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE)
            url: URL to request (can be relative to base_url or absolute)
            **kwargs: Additional arguments to pass to requests

        Returns:
            requests.Response object
        """
        # Make URL absolute if it's relative
        if not url.startswith("http"):
            url = f"{self.base_url}{url}"

        # Ensure headers dict exists and add authorization
        if "headers" not in kwargs:
            kwargs["headers"] = {}
        kwargs["headers"]["Authorization"] = f"Bearer {self.token}"

        wait_time = self.initial_wait
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                response = requests.request(method, url, **kwargs)

                # Handle 401 - reauthenticate and retry
                if response.status_code == 401:
                    click.echo("Received 401, reauthenticating...", err=True)
                    self._authenticate()
                    # Update token in headers
                    kwargs["headers"]["Authorization"] = f"Bearer {self.token}"
                    # Retry the request immediately after reauthentication
                    response = requests.request(method, url, **kwargs)

                # Handle 500/502 - retry with exponential backoff
                if response.status_code in (500, 502) and attempt < self.max_retries:
                    click.echo(
                        f"Server error {response.status_code}, retrying in {wait_time}s "
                        f"(attempt {attempt + 1}/{self.max_retries})...",
                        err=True,
                    )
                    time.sleep(wait_time)
                    wait_time *= 2
                    continue

                return response

            except requests.exceptions.RequestException as e:
                last_exception = e
                if attempt < self.max_retries:
                    click.echo(
                        f"Request error: {e}, retrying in {wait_time}s "
                        f"(attempt {attempt + 1}/{self.max_retries})...",
                        err=True,
                    )
                    time.sleep(wait_time)
                    wait_time *= 2
                    continue
                raise

        # If we exhausted retries, raise the last exception or return last response
        if last_exception:
            raise last_exception
        return response

    def get(self, url, **kwargs):
        """Make an authenticated GET request"""
        return self.request("GET", url, **kwargs)

    def post(self, url, **kwargs):
        """Make an authenticated POST request"""
        return self.request("POST", url, **kwargs)

    def put(self, url, **kwargs):
        """Make an authenticated PUT request"""
        return self.request("PUT", url, **kwargs)

    def patch(self, url, **kwargs):
        """Make an authenticated PATCH request"""
        return self.request("PATCH", url, **kwargs)

    def delete(self, url, **kwargs):
        """Make an authenticated DELETE request"""
        return self.request("DELETE", url, **kwargs)


class DateTimeEncoder(JSONEncoder):
    """JSON encoder that handles datetime objects"""

    def default(self, o):
        if isinstance(o, (datetime.date, datetime.datetime)):
            return o.isoformat()
        if isinstance(o, bytes):
            return o.decode("utf-8", errors="ignore")
        if isinstance(o, PosixPath):
            return str(o)
        return super().default(o)


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
            yield row["Key"], row.get("Size", 0), row["ETag"], row["LastModified"]
        else:
            key = row["Key"]
            total += len(rs.get("Contents", []))
    print("%d rows returned for s3://%s/%s" % (total, bucket, prefix))


def sum_bucket(s3, bucket, print_every=1000):
    """Summarize bucket contents by directory"""
    d = {}
    for i, (key, size, etag, last_modified) in enumerate(list_bucket(s3, bucket)):
        directory_name = "/".join(key.split("/")[0:-1]) + "/" if "/" in key else ""
        sz, items = d.get(directory_name, (0, 0))
        sz += size
        items += 1
        d[directory_name] = (sz, items)

        if i % print_every == 0:
            print(" --", i, directory_name, d[directory_name])

    for k, v in sorted(d.items(), key=lambda x: x[1][0], reverse=True):
        print(f"{k:15} {v[1]:,} {v[0] / 1024**3:.3}")

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


def get_icloud_from_stored_credentials(credential_id=None, user_id=None):
    """Get authenticated iCloud API from stored credentials in database

    Args:
        credential_id: Specific credential ID to use (optional)
        user_id: User ID to get credentials for (optional)

    Returns:
        PyiCloudService instance or None if no valid credentials found
    """
    from app.apple_auth import AppleAuthService
    from app.database import SessionLocal
    from sqlmodel import select

    db = SessionLocal()
    try:
        apple_auth_service = AppleAuthService()

        if credential_id:
            # Use specific credential
            api = apple_auth_service.get_authenticated_api(db, credential_id)
            if api:
                click.echo(f"Using stored Apple credentials (ID: {credential_id})")
                return api
            else:
                click.echo(
                    f"No valid authenticated session found for credential ID {credential_id}. "
                    "Please authenticate via the web interface at /settings/apple",
                    err=True,
                )
                return None
        elif user_id:
            # Get first active credential for user
            from app.models import AppleCredential

            credential = db.exec(
                select(AppleCredential)
                .where(
                    AppleCredential.user_id == user_id,
                    AppleCredential.is_active == True,
                )
                .order_by(AppleCredential.last_authenticated_at.desc())
            ).first()

            if credential:
                api = apple_auth_service.get_authenticated_api(db, credential.id)
                if api:
                    click.echo(
                        f"Using stored Apple credentials for {credential.apple_id}"
                    )
                    return api
                else:
                    click.echo(
                        "No valid authenticated session found. "
                        "Please authenticate via the web interface at /settings/apple",
                        err=True,
                    )
                    return None
            else:
                click.echo(
                    "No Apple credentials found in database. "
                    "Please add credentials via the web interface at /settings/apple",
                    err=True,
                )
                return None
        else:
            click.echo("Either credential_id or user_id must be provided", err=True)
            return None
    finally:
        db.close()
