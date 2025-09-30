from django.urls import path
from . import views

app_name = "converter"

urlpatterns = [
    path("", views.upload_view, name="upload"),
    path("result/<int:upload_id>/", views.result_view, name="result"),
]
