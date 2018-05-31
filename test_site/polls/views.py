# -*- coding: utf-8 -*-
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy

from django_sorcery.routers import action
from django_sorcery.viewsets import ModelViewSet

from .models import Question, Choice, db


class PollsViewSet(ModelViewSet):
    model = Question
    fields = "__all__"
    destroy_success_url = reverse_lazy("polls:question-list")

    def get_success_url(self):
        return reverse("polls:question-detail", kwargs={"pk": self.object.pk})

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
