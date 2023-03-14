from django import forms
from .models import Document, Project, DocumentComments, Evaluation, PlagiarismCheck
from django.utils.timezone import now


class DocumentCommentsForm(forms.ModelForm):
    class Meta:
        model = DocumentComments
        fields = ("comment", "commented_document")

    def __init__(self, user, document, *args, **kwargs):
        self.user = user
        self.document = document
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.user = self.user
        instance.document = self.document
        self.document.latest_update = now()
        self.document.save()
        if commit:
            instance.save()

        return instance
    

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Evaluation
        fields = ("comment", "grade")

    def __init__(self, user, project, *args, **kwargs):
        self.user = user
        self.project = project
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.user = self.user
        instance.project = self.project
        if commit:
            instance.save()

        return instance
    
    def is_valid(self):
        is_valid = super().is_valid()
        grades = self.project.evaluation_set.all().values_list("grade")
        if grades and grades[0][0] != self.cleaned_data["grade"]:
            self.add_error(None, "Grade can't be different from your colleague")
            return False
        return is_valid


class PlagiarismCheckForm(forms.ModelForm):
    class Meta:
        model = PlagiarismCheck
        fields = ("comment", "approved")

    def __init__(self, user, project, *args, **kwargs):
        self.user = user
        self.project = project
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.user = self.user
        instance.project = self.project
        if commit:
            instance.save()

        return instance


class UploadDocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ("file", "abstract")

    def __init__(self, project, *args, **kwargs):
        self.project = project
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.project = self.project
        instance.latest_update = now()
        if commit:
            instance.save()

        return instance


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ("supervisor",)

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        self.fields['supervisor'].queryset = self.fields['supervisor'].queryset.exclude(id=self.user.id)

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.student = self.user
        if commit:
            instance.save()

        return instance
