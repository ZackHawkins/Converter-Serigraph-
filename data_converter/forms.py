from django import forms

class UploadForm(forms.Form):
    file = forms.FileField(
        label="Choose TXT file",
        help_text="Upload a GHSP-style pipe-delimited TXT file."
    )

    def clean_file(self):
        f = self.cleaned_data["file"]
        if not f.name.lower().endswith(".txt"):
            raise forms.ValidationError("Please upload a .TXT file")
        return f
