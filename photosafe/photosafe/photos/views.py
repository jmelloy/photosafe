from django.db.models import Count, Max
from django.db.models.functions import Coalesce
from django.db.models.functions.datetime import ExtractDay, ExtractMonth, ExtractYear
from django.http.response import JsonResponse
from django.views import View

from photosafe.photos.models import Photo

# Create your views here.


class PhotoDayView(View):
    def get(self, request):
        rs = Photo.objects.values(
            year=ExtractYear("date"),
            month=ExtractMonth("date"),
            day=ExtractDay("date"),
        ).annotate(count=Count("*"), max_date=Max(Coalesce("date", "date_modified")))

        return JsonResponse([dict(r) for r in rs], safe=False)
