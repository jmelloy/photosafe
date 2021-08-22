from django.urls import path

from photosafe.users.views import (
    current_user_view,
    user_detail_view,
    user_redirect_view,
    user_update_view,
)

app_name = "users"
urlpatterns = [
    path("~redirect/", view=user_redirect_view, name="redirect"),
    path("~update/", view=user_update_view, name="update"),
    path("me/", view=current_user_view, name="me"),
    path("<str:username>/", view=user_detail_view, name="detail"),
]
