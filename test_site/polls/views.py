# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy

from django_sorcery.formsets import inlineformset_factory
from django_sorcery.routers import action
from django_sorcery.viewsets import ModelViewSet

from .models import Choice, Question, db


ChoiceFormSet = inlineformset_factory(relation=Question.choices, fields=(Choice.choice_text.key,), session=db)


class PollsViewSet(ModelViewSet):
    model = Question
    fields = (Question.question_text.key, Question.pub_date.key)
    destroy_success_url = reverse_lazy("polls:question-list")

    def get_success_url(self):
        return reverse("polls:question-detail", kwargs={"pk": self.object.pk})

    def get_form_context_data(self, **kwargs):
        kwargs["choice_set"] = self.get_choice_formset()
        return super(PollsViewSet, self).get_form_context_data(**kwargs)

    def get_choice_formset(self, instance=None):
        if not hasattr(self, "_choice_formset"):
            instance = instance or self.object
            self._choice_formset = ChoiceFormSet(
                instance=instance, data=self.request.POST if self.request.POST else None
            )

        return self._choice_formset

    def process_form(self, form):
        if form.is_valid() and self.get_choice_formset(instance=form.instance).is_valid():
            return self.form_valid(form)

        return form.invalid(self, form)

    def form_valid(self, form):
        self.object = form.save()
        self.object.choices = self.get_choice_formset().save()
        db.flush()
        return HttpResponseRedirect(self.get_success_url())

    @action(detail=True)
    def results(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    @action(detail=True, methods=["POST"])
    def vote(self, request, *args, **kwargs):
        self.object = self.get_object()

        selected_choice = Choice.query.filter(
            Choice.question == self.object, Choice.pk == request.POST.get("choice")
        ).one_or_none()

        if not selected_choice:
            context = self.get_detail_context_data(object=self.object)
            context["error_message"] = "You didn't select a choice."
            self.action = "retrieve"
            return self.render_to_response(context)

        selected_choice.votes += 1
        db.flush()
        return HttpResponseRedirect(reverse("polls:question-results", args=(self.object.pk,)))
