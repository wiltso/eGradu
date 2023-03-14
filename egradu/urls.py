from django.urls import path
from egradu import views
from django.contrib.auth.decorators import login_required

urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("", login_required(views.IndexView.as_view()), name="index"),
    path("student_index/", login_required(views.StudentIndexView.as_view()), name="student_index"),
    path("project_create/", views.ProjectView.as_view(), name="project_create"),
    path("upload_document/", views.UploadDocumentView.as_view(), name="upload_document"),
    path("document/<int:pk>/", views.DocumentView.as_view(), name="document"),
    path("start_lang_check/<int:pk>/", views.StartLanguageCheck.as_view(), name="start_lang_check"),
    path("teacher_index/", views.TeacherIndexView.as_view(), name="teacher_index"),
    path("project/<int:pk>/", views.TeacherProjectView.as_view(), name="project"),
    path("review/<int:pk>/", views.ReviewView.as_view(), name="review"),
    path("second_review/<int:pk>/", views.SecondReviewView.as_view(), name="review"),
    path("start_plagiarism/<int:pk>/", views.SendToPlagiarism.as_view(), name="start_plagiarism"),
    path("start_review/<int:pk>/", views.StartReview.as_view(), name="start_review"),
    path("import_plagiarism/<int:pk>/", views.ImportPlagiarism.as_view(), name="import_plagiarism")
]
