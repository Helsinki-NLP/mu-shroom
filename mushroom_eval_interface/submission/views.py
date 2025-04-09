from django.db.models import Count
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views import generic
from django.contrib.auth import forms as auth_forms


# Create your views here.
from django.http import HttpResponse
from . import forms, services, models

# Create your views here.

def index(request):
    context = {"profile": services.get_profile(request.user)} if request.user.is_authenticated else {}
    df_rankings = services.get_rankings()
    if df_rankings is not None:
        context['rankings'] = {
            lang: (
                df_rankings[df_rankings.language == lang]
                .sort_values('avg_iou_score', ascending=False)
                .to_dict(orient='records')
            )
            for lang in sorted(df_rankings.language.unique())
        }
    return render(
        request,
        "submission/index.html",
        context,
    )

class SignUpView(generic.CreateView):
    form_class = forms.UserAndPreferencesCreationForm
    success_url = reverse_lazy("login")
    template_name = "registration/signup.html"


@login_required
def make_submission(request):
    # if this is a POST request we need to process the form data
    can_submit = services.can_submit()
    if request.method == "POST" and can_submit:
        # create a form instance and populate it with data from the request:
        form = forms.SubmissionUploadForm(request.POST, request.FILES)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            profile = services.get_profile(request.user)
            for pred_dicts in form.cleaned_data['files']:
                services.handle_valid_file(
                    pred_dicts, 
                    form.cleaned_data, 
                    profile,
                )
            # redirect to a new URL:
            return redirect("index")

    # if a GET (or any other method) we'll create a blank form
    else:
        form = forms.SubmissionUploadForm() if can_submit else None

    return render(request, "submission/submission.html", {"form": form, 'can_submit': can_submit})
    

class PastSubmissionsView(LoginRequiredMixin, generic.ListView):
    template_name = "submission/past.html"
    context_object_name = "past_submissions"

    def get_queryset(self):
        profile = services.get_profile(self.request.user)
        return models.Submission.objects.filter(submitter=profile).all()


class DeleteSubmissionView(LoginRequiredMixin, generic.edit.DeleteView):
    model = models.Submission
    success_url = reverse_lazy("past_submissions")

    def form_valid(self, form):
        self.object = self.get_object()
        success_url = self.get_success_url()
        if self.object.submitter.id == services.get_profile(self.request.user).id:
            self.object.delete()
            return redirect(success_url)
        else:
            return HttpResponseForbidden(f"Cannot delete others' submissions. <a href=\"{success_url}\">Go back</a>.")


class SubmissionUpdateView(generic.edit.UpdateView):
    model = models.Submission
    form_class = forms.SubmissionMetadataForm
    template_name_suffix = "_update_form"
    success_url = reverse_lazy("past_submissions")

