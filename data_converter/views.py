import os
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.text import slugify
from django.views.decorators.http import require_http_methods

from .forms import UploadForm
from .models import Upload, Export
from .parser import parse_txt_to_rows, generate_csv_content

@require_http_methods(["GET", "POST"])
def upload_view(request):
    if request.method == "POST":
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            up = Upload.objects.create(
                file=form.cleaned_data["file"],
                original_name=form.cleaned_data["file"].name
            )
            # parse + create csv
            txt_bytes = up.file.read()
            txt_str = txt_bytes.decode("utf-8", errors="replace")
            rows = parse_txt_to_rows(txt_str)
            csv_bytes = generate_csv_content(rows)

            base = os.path.splitext(os.path.basename(up.file.name))[0]
            csv_name = f"{slugify(base)}.csv"
            out_path = os.path.join(settings.MEDIA_ROOT, "exports")
            os.makedirs(out_path, exist_ok=True)
            full_path = os.path.join(out_path, csv_name)

            with open(full_path, "wb") as f:
                f.write(csv_bytes)

            rel_media_path = f"exports/{csv_name}"
            exp = Export.objects.create(upload=up, csv_file=rel_media_path, rows=len(rows))
            return redirect(reverse("converter:result", args=[up.id]))
    else:
        form = UploadForm()
    return render(request, "converter/upload.html", {"form": form})

def result_view(request, upload_id: int):
    up = get_object_or_404(Upload, pk=upload_id)
    exp = up.exports.order_by("-created_at").first()
    return render(request, "converter/result.html", {"upload": up, "export": exp})
