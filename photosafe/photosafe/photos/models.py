from django.db import models

# Create your models here.

class Photo(models.Model):
    uuid = models.TextField(primary_key=True)
    masterFingerprint = models.TextField(unique=True)

    filename = models.TextField()
    original_filename = models.TextField()
    date = models.DateTimeField()
    description = models.TextField()
    title = models.TextField()
    keywords = models.JSONField()
    labels = models.JSONField()
    albums = models.JSONField()
    folders = models.JSONField()
    persons = models.JSONField()
    faces = models.JSONField()
    path = models.TextField()

    ismissing =models.BooleanField()
    hasadjustments =models.BooleanField()
    external_edit =models.BooleanField()
    favorite =models.BooleanField()
    hidden =models.BooleanField()
    latitude =models.FloatField()
    longitude =models.FloatField()
    path_edited =models.TextField()
    shared =models.BooleanField()
    isphoto =models.BooleanField()
    ismovie =models.BooleanField()
    uti =models.TextField()
    uti_original =models.TextField()
    burst =models.BooleanField()
    live_photo =models.BooleanField()
    path_live_photo =models.TextField()
    iscloudasset =models.BooleanField()
    incloud =models.BooleanField()
    date_modified =models.DateTimeField()
    portrait =models.BooleanField()
    screenshot =models.BooleanField()
    slow_mo =models.BooleanField()
    time_lapse =models.BooleanField()
    hdr =models.BooleanField()
    selfie =models.BooleanField()
    panorama =models.BooleanField()
    has_raw =models.BooleanField()
    israw =models.BooleanField()
    raw_original =models.BooleanField()
    uti_raw =models.TextField()
    path_raw =models.TextField()
    place =models.JSONField()
    exif =models.JSONField()
    score =models.JSONField()
    intrash =models.BooleanField()
    height =models.IntegerField()
    width =models.IntegerField()
    orientation =models.IntegerField()
    original_height =models.IntegerField()
    original_width =models.IntegerField()
    original_orientation =models.IntegerField()
    original_filesize =models.IntegerField()
    comments =models.JSONField()
    likes =models.JSONField()
    search_info =models.JSONField()


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
