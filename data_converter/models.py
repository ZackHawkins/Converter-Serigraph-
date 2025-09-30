from django.db import models
from django.urls import reverse

class Upload(models.Model):
    file = models.FileField(upload_to="uploads/")
    created_at = models.DateTimeField(auto_now_add=True)
    original_name = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.original_name or self.file.name

    def get_absolute_url(self):
        return reverse("converter:result", args=[self.id])

class Export(models.Model):
    upload = models.ForeignKey(Upload, on_delete=models.CASCADE, related_name="exports")
    csv_file = models.FileField(upload_to="exports/")
    rows = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.csv_file.name