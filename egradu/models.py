from django.utils.translation import gettext_lazy as _
from django.db import models
from django_enumfield import enum
from django.contrib.auth import get_user_model


User = get_user_model()


class DocumentStatus(enum.Enum):
    DRAFT = 0
    PENDING_LANGUAGE_CHECK = 10
    LANGUAGE_CHECK = 11
    PENDING_PLAGIARISM = 20
    PLAGIARISM_ONGOING = 21
    PLAGIARISM = 22
    EVALUATION = 30
    PENDING_APPROVAL = 40
    APPROVED = 41
    DENIED = 42

    __labels__ = {
        DRAFT: _("Draft"),
        PENDING_LANGUAGE_CHECK: _("Pending language check"),
        LANGUAGE_CHECK: _("language checked"),
        PENDING_PLAGIARISM: _("Pending plagiarism"),
        PLAGIARISM_ONGOING: _("Plagiarism ongoing"),
        PLAGIARISM: _("Plagiarism completed"),
        EVALUATION: _("Evaluation ongoing"),
        PENDING_APPROVAL: _("Pending dean approval"),
        APPROVED: _("Approved"),
        DENIED: _("Denied"),
    }

    __transitions__ = {
        PENDING_LANGUAGE_CHECK: (DRAFT,),
        LANGUAGE_CHECK: (PENDING_LANGUAGE_CHECK,),
        PENDING_PLAGIARISM: (LANGUAGE_CHECK,),
        PLAGIARISM_ONGOING: (PENDING_PLAGIARISM,),
        PLAGIARISM: (PLAGIARISM_ONGOING,),
        EVALUATION: (PLAGIARISM,),
        PENDING_APPROVAL: (EVALUATION,),
        APPROVED: (PENDING_APPROVAL,),
        DENIED: (PENDING_APPROVAL),
    }

    __default__ = DRAFT

class Grade(enum.Enum):
    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5

    __labels__ = {
        ONE: _("1"),
        TWO: _("2"),
        THREE: _("3"),
        FOUR: _("4"),
        FIVE: _("5"),
    }


class UserType(models.Model):
    name = models.CharField(max_length=255)
    identifier = models.CharField(max_length=255)


class Project(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="project_student")
    supervisor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="project_supervisor")
    reviewers = models.ManyToManyField(User, related_name="project_reviewer")
    final_version = models.ForeignKey("Document", on_delete=models.CASCADE, null=True, related_name="projects")
    status = enum.EnumField(DocumentStatus)


class Document(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True)
    file = models.FileField()
    abstract = models.FileField(null=True, blank=True)
    uploaded = models.DateTimeField(auto_now_add=True)
    latest_update = models.DateTimeField(null=True, blank=True)
    draft = models.BooleanField(default=True)


class LastDocumentVisit(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    time = models.DateTimeField(auto_now_add=True)


class DocumentComments(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    commented_document = models.FileField(blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField()


class CheckBase(models.Model):
    class Meta:
        abstract = True

    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    comment = models.TextField()
    grade = enum.EnumField(Grade)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    

class LanguageCheck(CheckBase):
    pass


class PlagiarismCheck(CheckBase):
    grade = None
    approved = models.BooleanField(null=True)


class Evaluation(CheckBase):
    other_reviewer = models.ForeignKey(
        User, on_delete=models.CASCADE,
        null=True,related_name="other_reviewer",
        verbose_name="Your suggested other reviewer"
    )


class Contact(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    types = models.ManyToManyField(UserType)
