from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView as DJLoginView, LogoutView as DJLogoutView
from django.views.generic import TemplateView, FormView, DetailView
from .forms import UploadDocumentForm, ProjectForm, DocumentCommentsForm, ReviewForm, PlagiarismCheckForm, Evaluation
from .models import Project, Document, DocumentStatus, LastDocumentVisit
from django.db.models import Case, When, OuterRef, Subquery, BooleanField
# Create your views here.


class LogoutView(DJLogoutView):
    pass


class LoginView(DJLoginView):
    template_name = "egradu/login.html"


class IndexView(TemplateView):
    template_name = "egradu/index.html"

    def dispatch(self, request, *args, **kwargs):
        contact = request.user.contact
        if (
            contact.types.filter(identifier="student").exists() and not
            Project.objects.filter(student=request.user).exists()
        ):
            return redirect("project_create")
        if contact.types.filter(identifier="student").exists():
            return redirect("student_index")
        elif contact.types.filter(identifier="teacher").exists():
            return redirect("teacher_index")

        return super().dispatch(request, *args, **kwargs)
    

class TeacherIndexView(TemplateView):
    template_name = "egradu/teacher_index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        projects = Project.objects.filter(supervisor=self.request.user)

        subquery = LastDocumentVisit.objects.filter(
            document=OuterRef('pk'),
            user=self.request.user
        ).order_by("-time").values('time')[:1]

        documents = Document.objects.filter(project__in=projects, project__status__lte=20).annotate(
            update=Case(
                When(latest_update__lt=Subquery(subquery), then=False),
                default=True,
                output_field=BooleanField(),
            )
        ).order_by("-uploaded")

        send_to_plagiarism = documents.filter(project__status=DocumentStatus.PENDING_PLAGIARISM)

        documents = documents.filter(project__status__lt=20)

        pending_plagiarism = Project.objects.filter(document__id__in=send_to_plagiarism.values_list("id")).distinct()

        context["drafts"] = documents.filter(draft=True)
        context["documents"] = documents.exclude(
            draft=True,
            project__status=DocumentStatus.PENDING_PLAGIARISM
        )
        evaluations = Evaluation.objects.filter(user=self.request.user)
        context["reviews"] = Project.objects.filter(reviewers=self.request.user).exclude(id__in=evaluations.values_list("project_id"))
        context["pending_plagiarism"] = pending_plagiarism
        context["projects"] = projects.exclude(
            reviewers=self.request.user,
            document__id__in=documents.exclude(draft=True, project__status=DocumentStatus.PENDING_PLAGIARISM).values_list("id"),
            id__in=pending_plagiarism.values_list("id"),
        )
        return context
    

class SecondReviewView(FormView, DetailView):
    form_class = ReviewForm
    model = Project
    template_name = "egradu/second_review.html"
    success_url = "/"
    
    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["project"] = self.object
        return kwargs

    def form_valid(self, form):
        form.save()
        review_count = self.object.evaluation_set.all().count()
        if self.object.reviewers.all().count() <= review_count:
            self.object.status = DocumentStatus.PENDING_APPROVAL
            self.object.save()
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = self.object
        context["document"] = self.object.final_version
        print(dir(self.object))
        context["past_reviews"] = self.object.evaluation_set.all()
        return context

class ReviewView(FormView, DetailView):
    form_class = ReviewForm
    model = Project
    template_name = "egradu/review.html"
    success_url = "/"

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["project"] = self.object
        return kwargs

    def form_valid(self, form):
        form.save()
        review_count = self.object.evaluation_set.all().count()
        if self.object.reviewers.all().count() <= review_count:
            self.object.status = DocumentStatus.PENDING_APPROVAL
            self.object.save()
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = self.object
        context["document"] = self.object.final_version
        return context


class TeacherProjectView(DetailView):
    template_name = "egradu/project.html"
    model = Project

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.object

        subquery = LastDocumentVisit.objects.filter(
            document=OuterRef('pk'),
            user=self.request.user
        ).order_by("-time").values('time')[:1]

        documents = Document.objects.filter(project=project).annotate(
            update=Case(
                When(latest_update__lt=Subquery(subquery), then=False),
                default=True,
                output_field=BooleanField(),
            )
        ).order_by("-uploaded")

        
        context["document"] = documents[0]
        context["documents"] = documents[1:]
        context["project"] = project
        return context


class StudentIndexView(TemplateView):
    template_name = "egradu/student_index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = Project.objects.filter(student=self.request.user).first()

        subquery = LastDocumentVisit.objects.filter(
            document=OuterRef('pk'),
            user=self.request.user
        ).order_by("-time").values('time')[:1]

        documents = Document.objects.filter(project=project).annotate(
            update=Case(
                When(latest_update__lt=Subquery(subquery), then=False),
                default=True,
                output_field=BooleanField(),
            ),
            update_time=Subquery(subquery)
        ).order_by("-uploaded")

        context["document"] = documents[0] if len(documents) else None
        context["documents"] = documents[1:]
        context["project"] = project
        context["evaluations"] = project.evaluation_set.all()
        context["languagecheck"] = project.languagecheck_set.all()
        context["plagiarism_check"] = project.plagiarismcheck_set.all()
        
        return context


class ProjectView(FormView):
    template_name = "egradu/project_view.html"
    form_class = ProjectForm
    success_url = "/"

    def dispatch(self, request, *args, **kwargs):
        contact = request.user.contact
        if (
            contact.types.filter(identifier="student").exists() and
            Project.objects.filter(student=request.user).exists()
        ):
            return redirect("index")
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs
    

class DocumentView(FormView, DetailView):
    template_name = "egradu/document_view.html"
    form_class = DocumentCommentsForm
    model = Document
    success_url = "/"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["document"] = self.get_object()
        return kwargs

    def form_valid(self, form):
        form.save()
        LastDocumentVisit.objects.create(document=self.get_object(), user=self.request.user)
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        LastDocumentVisit.objects.create(document=self.object, user=self.request.user)
        context["object"] = self.object
        context["comments"] = self.object.documentcomments_set.all()
        return context


class UploadDocumentView(FormView):
    template_name = "egradu/upload_document.html"
    success_url = "/student_index/"
    form_class = UploadDocumentForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        project = Project.objects.filter(student=self.request.user).first()
        kwargs["project"] = project
        return kwargs

    def form_valid(self, form):
        obj = form.save()
        LastDocumentVisit.objects.create(document=obj, user=self.request.user)
        return super().form_valid(form)


class StartLanguageCheck(DetailView):
    model = Document

    def dispatch(self, request, *args, **kwargs):
        document = self.get_object()
        project = document.project
        document.draft = False
        document.save()
        project.status = DocumentStatus.PENDING_LANGUAGE_CHECK
        project.save()
        return redirect("index")


class StartReview(DetailView):
    model = Project

    def dispatch(self, request, *args, **kwargs):
        project = self.get_object()

        subquery = LastDocumentVisit.objects.filter(
            document=OuterRef('pk'),
            user=self.request.user
        ).order_by("-time").values('time')[:1]

        documents = Document.objects.filter(project=project).annotate(
            update=Case(
                When(latest_update__lt=Subquery(subquery), then=False),
                default=True,
                output_field=BooleanField(),
            )
        ).order_by("-uploaded")

        document = documents[0]
        project.final_version = document
        project.status = DocumentStatus.PENDING_PLAGIARISM
        project.save()
        return redirect("index")
    

class ImportPlagiarism(FormView, DetailView):
    model = Project
    form_class = PlagiarismCheckForm
    success_url = "/"
    template_name = "egradu/plagiarism.html"

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["project"] = self.object
        return kwargs

    def form_valid(self, form):
        check = form.save()
        self.object.status = DocumentStatus.PLAGIARISM
        self.object.save()
        if check.approved:
            self.object.status = DocumentStatus.EVALUATION
            self.object.save()
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = self.object
        context["document"] = self.object.final_version
        return context


class SendToPlagiarism(DetailView):
    model = Project

    def dispatch(self, request, *args, **kwargs):
        project = self.get_object()
        project.status = DocumentStatus.PLAGIARISM_ONGOING
        project.save()
        return redirect("index")
