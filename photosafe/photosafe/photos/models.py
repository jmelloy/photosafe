from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField
from django.db import models

# Create your models here.


class Photo(models.Model):
    uuid = models.UUIDField(primary_key=True)
    masterFingerprint = models.TextField(null=True)

    original_filename = models.TextField()
    date = models.DateTimeField()
    description = models.TextField(null=True, blank=True)
    title = models.TextField(null=True, blank=True)
    keywords = ArrayField(models.TextField(), null=True, blank=True)
    labels = ArrayField(models.TextField(), null=True, blank=True)
    albums = ArrayField(models.TextField(), null=True, blank=True)
    # folders = models.JSONField(null=True)
    persons = ArrayField(models.TextField(), null=True, blank=True)
    faces = models.JSONField(null=True)
    # path = models.TextField(null=True, blank=True)

    # ismissing = models.BooleanField(null=True)
    # hasadjustments = models.BooleanField(null=True)
    # external_edit = models.BooleanField(null=True)
    favorite = models.BooleanField(null=True)
    hidden = models.BooleanField(null=True)
    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)
    # path_edited = models.TextField(null=True, blank=True)
    # shared = models.BooleanField(null=True)
    isphoto = models.BooleanField(null=True)
    ismovie = models.BooleanField(null=True)
    uti = models.TextField(null=True, blank=True)
    # uti_original = models.TextField(null=True, blank=True)
    burst = models.BooleanField(null=True)
    live_photo = models.BooleanField(null=True)
    # path_live_photo = models.TextField(null=True, blank=True)
    # iscloudasset = models.BooleanField(null=True)
    # incloud = models.BooleanField(null=True)
    date_modified = models.DateTimeField(null=True)
    portrait = models.BooleanField(null=True)
    screenshot = models.BooleanField(null=True)
    slow_mo = models.BooleanField(null=True)
    time_lapse = models.BooleanField(null=True)
    hdr = models.BooleanField(null=True)
    selfie = models.BooleanField(null=True)
    panorama = models.BooleanField(null=True)
    # has_raw = models.BooleanField(null=True)
    # israw = models.BooleanField(null=True)
    # raw_original = models.BooleanField(null=True)
    # uti_raw = models.TextField(null=True, blank=True)
    # path_raw = models.TextField(null=True, blank=True)
    place = models.JSONField(null=True)
    exif = models.JSONField(null=True)
    score = models.JSONField(null=True)
    intrash = models.BooleanField(null=True)
    height = models.IntegerField(null=True)
    width = models.IntegerField(null=True)
    size = models.IntegerField(null=True)
    orientation = models.IntegerField(null=True)
    # original_height = models.IntegerField(null=True)
    # original_width = models.IntegerField(null=True)
    # original_orientation = models.IntegerField(null=True)
    # original_filesize = models.IntegerField(null=True)
    # comments = models.JSONField(null=True)
    # likes = models.JSONField(null=True)
    search_info = models.JSONField(null=True)

    s3_key_path = models.TextField(null=True, blank=True)
    s3_thumbnail_path = models.TextField(null=True, blank=True)
    s3_edited_path = models.TextField(null=True, blank=True)
    s3_original_path = models.TextField(null=True, blank=True)
    s3_live_path = models.TextField(null=True, blank=True)

    owner = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)

    library = models.TextField(null=True, blank=True)


class Version(models.Model):
    photo = models.ForeignKey(
        Photo,
        related_name="versions",
        on_delete=models.CASCADE,
        db_column="photo_uuid",
    )

    version = models.TextField()
    s3_path = models.TextField()
    filename = models.TextField(null=True, blank=True)
    width = models.IntegerField(null=True)
    height = models.IntegerField(null=True)
    size = models.IntegerField(null=True)
    type = models.TextField(null=True, blank=True)


class Album(models.Model):
    uuid = models.UUIDField(primary_key=True)
    title = models.TextField(null=False, blank=True)
    creation_date = models.DateTimeField(null=True)
    start_date = models.DateTimeField(null=True)
    end_date = models.DateTimeField(null=True)

    photos = models.ManyToManyField(Photo)


# library <class 'str'> /Users/jmelloy/Pictures/Photos Library.photoslibrary
# uuid <class 'str'> FD2E9C5F-1FA6-4CB9-844A-F2D108531AD5
# filename <class 'str'> FD2E9C5F-1FA6-4CB9-844A-F2D108531AD5.jpeg
# original_filename <class 'str'> 100_1202.JPG
# date <class 'datetime.datetime'> 2009-08-04 00:57:54-07:00
# description <class 'NoneType'> None
# title <class 'NoneType'> None
# keywords <class 'list'> []
# labels <class 'list'> ['Plant', 'Land', 'Outdoor']
# albums <class 'list'> []
# folders <class 'dict'> {}
# persons <class 'list'> []
# faces <class 'list'> []
# path <class 'str'> /Users/jmelloy/Pictures/Photos Library.photoslibrary/originals/F/FD2E9C5F-1FA6-4CB9-844A-F2D108531AD5.jpeg
# ismissing <class 'bool'> False
# hasadjustments <class 'bool'> False
# external_edit <class 'bool'> False
# favorite <class 'bool'> False
# hidden <class 'bool'> False
# latitude <class 'NoneType'> None
# longitude <class 'NoneType'> None
# path_edited <class 'NoneType'> None
# shared <class 'bool'> False
# isphoto <class 'bool'> True
# ismovie <class 'bool'> False
# uti <class 'str'> public.jpeg
# uti_original <class 'str'> public.jpeg
# burst <class 'bool'> False
# live_photo <class 'bool'> False
# path_live_photo <class 'NoneType'> None
# iscloudasset <class 'bool'> True
# incloud <class 'bool'> True
# date_modified <class 'NoneType'> None
# portrait <class 'bool'> False
# screenshot <class 'bool'> False
# slow_mo <class 'bool'> False
# time_lapse <class 'bool'> False
# hdr <class 'bool'> False
# selfie <class 'bool'> False
# panorama <class 'bool'> False
# has_raw <class 'bool'> False
# israw <class 'bool'> False
# raw_original <class 'bool'> False
# uti_raw <class 'NoneType'> None
# path_raw <class 'NoneType'> None
# place <class 'dict'> {}
# exif <class 'dict'> {'flash_fired': True, 'iso': 200, 'metering_mode': 5, 'sample_rate': None, 'track_format': None, 'white_balance': 0, 'aperture': 2.7, 'bit_rate': None, 'duration': None, 'exposure_bias': 0.0, 'focal_length': 6.0, 'fps': None, 'latitude': None, 'longitude': None, 'shutter_speed': 0.008772, 'camera_make': 'EASTMAN KODAK COMPANY', 'camera_model': 'KODAK EASYSHARE C713 ZOOM DIGITAL CAMERA', 'codec': None, 'lens_model': None}
# score <class 'dict'> {'overall': 0.305419921875, 'curation': 0.5, 'promotion': 0.0, 'highlight_visibility': 0.038931297721298594, 'behavioral': 0.10000000149011612, 'failure': -0.0008006095886230469, 'harmonious_color': 0.005634307861328125, 'immersiveness': 0.0087432861328125, 'interaction': 0.009999999776482582, 'interesting_subject': -0.626953125, 'intrusive_object_presence': -0.02874755859375, 'lively_color': 0.263427734375, 'low_light': 0.00035262107849121094, 'noise': -0.0091552734375, 'pleasant_camera_tilt': -0.037506103515625, 'pleasant_composition': -0.28173828125, 'pleasant_lighting': -0.0242919921875, 'pleasant_pattern': 0.050689697265625, 'pleasant_perspective': -0.051513671875, 'pleasant_post_processing': -0.00152587890625, 'pleasant_reflection': -0.006771087646484375, 'pleasant_symmetry': 0.0024433135986328125, 'sharply_focused_subject': 0.01416778564453125, 'tastefully_blurred': 0.000843048095703125, 'well_chosen_subject': -0.015380859375, 'well_framed_subject': -0.14892578125, 'well_timed_shot': -0.0157623291015625}
# intrash <class 'bool'> False
# height <class 'int'> 2292
# width <class 'int'> 3056
# orientation <class 'int'> 1
# original_height <class 'int'> 2292
# original_width <class 'int'> 3056
# original_orientation <class 'int'> 1
# original_filesize <class 'int'> 1126006
# comments <class 'list'> []
# likes <class 'list'> []
# search_info <class 'dict'> {'labels': ['Plant', 'Land', 'Outdoor'], 'place_names': [], 'streets': [], 'neighborhoods': [], 'city': '', 'locality_names': [], 'state': '', 'state_abbreviation': '', 'country': '', 'bodies_of_water': [], 'month': 'August', 'year': '2009', 'holidays': [], 'activities': ['Trip', 'Travel'], 'season': 'Summer', 'venues': [], 'venue_types': [], 'media_types': ['Photos']}
