import random

from django.db.models import Count
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views import generic

# Create your views here.
from django.http import HttpResponse
from . import models, forms, services

@login_required(login_url='/login/')
def index(request, preselected_annotation_id=None):
    if preselected_annotation_id is None:
        profile = services.get_profile(request.user)
        existing_annotations = set(
            models
            .Annotation
            .objects
            .filter(annotator__id=profile.id)
            .values_list('datapoint_id', flat=True)
        )
        n_annots_max = 3
        if profile.language in {'EN'}:
            n_annots_max = 5
        datapoint_to_annotate = (
            models
            .Datapoint
            .objects
            .annotate(num_annots=Count("annotation"))
            .filter(language=profile.language, num_annots__lt=n_annots_max)
            .exclude(id__in=existing_annotations)
            .order_by('?')
            .first()
        )
        if datapoint_to_annotate is None:
            return render(
                request,
                "annotation/annotation.html",
                {
                    'all_complete': True,
                }
            )
        return render(
            request,
            "annotation/annotation.html",
            {
                "all_complete": False,
                "datapoint": datapoint_to_annotate,
                "previous_annotation": None,
                "is_edit": "no",
            }
        )
    else:
        annotation = (
            models
            .Annotation
            .objects
            .get(pk=preselected_annotation_id)
        )

        return render(
            request,
            "annotation/annotation.html",
            {
                "all_complete": False,
                "datapoint": annotation.datapoint,
                "previous_annotation": annotation,
                "is_edit": "yes",
            }
        )



@login_required(login_url='/login/')
def post_annotation(request):
    data = request.POST
    datapoint = (
        models
        .Datapoint
        .objects
        .get(pk=data['iptdatapointid'])
    )
    profile = services.get_profile(request.user)
    is_update = data['iptisedit'] == 'yes'
    json_spans = services.annots_to_json_spans(
        data['iptselected'],
        datapoint.model_output,
        datapoint.hf_model_name,
    )
    if is_update:
        models.Annotation.objects.filter(
            datapoint__id=datapoint.id,
            annotator__id=profile.id,
        ).update(
            json_highlighted_spans=json_spans,
            comments=data['comments'],
        )
    else:
        (
            models
            .Annotation
            .objects
            .create(
                datapoint=datapoint,
                annotator=profile,
                json_highlighted_spans=json_spans,
                comments=data['comments'],
            )
        )
    return redirect("index" if not is_update else "past_annotations")

class SignUpView(generic.CreateView):
    form_class = forms.UserAndPreferencesCreationForm
    success_url = reverse_lazy("login")
    template_name = "registration/signup.html"

@login_required(login_url='/login/')
def edit(request, annotation_id):
    profile = services.get_profile(request.user)
    obj = models.Annotation.objects.get(pk=annotation_id)
    if obj.annotator.id != profile.id:
        return HttpResponseForbidden(f"Cannot edit others' annotations. <a href=\"{reverse('past_annotations')}\">Go back</a>.")
    return index(request, preselected_annotation_id=annotation_id)

class PastAnnotationsView(LoginRequiredMixin, generic.ListView):
    template_name = "annotation/past.html"
    context_object_name = "past_annotations"

    def get_queryset(self):
        profile = services.get_profile(self.request.user)
        return models.Annotation.objects.filter(annotator__id=profile.id).all()

class DeleteAnnotationView(LoginRequiredMixin, generic.edit.DeleteView):
    model = models.Annotation
    success_url = reverse_lazy("past_annotations")

    def form_valid(self, form):
        self.object = self.get_object()
        success_url = self.get_success_url()
        if self.object.annotator.id == services.get_profile(self.request.user).id:
            self.object.delete()
            return redirect(success_url)
        else:
            return HttpResponseForbidden(f"Cannot delete others' annotations. <a href=\"{success_url}\">Go back</a>.")
