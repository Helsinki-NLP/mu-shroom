from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("signup/", views.SignUpView.as_view(), name="signup"),
    path("make_submission/", views.make_submission, name="make_submission"),
    path("past_submissions/", views.PastSubmissionsView.as_view(), name="past_submissions"),
    path("<int:pk>/delete/", views.DeleteSubmissionView.as_view(), name="delete_submission"),
    path("<int:pk>/edit/", views.SubmissionUpdateView.as_view(), name="edit_submission"),
]
