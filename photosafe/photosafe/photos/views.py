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
        ).annotate(count=Count("*"), max_date=Max(Coalesce("date_modified", "date")))

        r = {}
        for row in rs:
            year = int(row["year"])
            month = int(row["month"])
            day = int(row["day"])

            if year not in r:
                r[year] = {}

            if month not in r[year]:
                r[year][month] = {}

            if day not in r[year][month]:
                r[year][month][day] = {
                    "count": int(row["count"]),
                    "max_date": row["max_date"],
                }

        return JsonResponse(r)
