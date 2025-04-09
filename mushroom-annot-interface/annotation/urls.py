from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("post_annotation/", views.post_annotation, name="post_annotation"),
    path("past_annotations/", views.PastAnnotationsView.as_view(), name="past_annotations"),
    path("<int:pk>/delete/", views.DeleteAnnotationView.as_view(), name="delete_annotation"),
    path("<int:annotation_id>/edit/", views.edit, name="edit_annotation"),
    path("signup/", views.SignUpView.as_view(), name="signup"),
]
