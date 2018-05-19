from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse

from django_sorcery.shortcuts import get_object_or_404
from django_sorcery import views

from .models import Question, Choice, db


class IndexView(views.ListView):
    template_name = 'polls/index.html'
    context_object_name = 'latest_question_list'

    def get_queryset(self):
        return Question.objects.order_by(Question.pub_date.desc())[:5]


class DetailView(views.DetailView):
    model = Question
    session = db
    template_name = 'polls/detail.html'


class ResultsView(DetailView):
    template_name = 'polls/results.html'


def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)

    selected_choice = Choice.query.filter(
        Choice.question == question,
        Choice.pk == request.POST['choice'],
    ).one_or_none()

    if not selected_choice:
        return render(request, 'polls/detail.html', {
            'question': question,
            'error_message': "You didn't select a choice.",
        })

    selected_choice.votes += 1
    db.flush()
    return HttpResponseRedirect(reverse('polls:results', args=(question.pk,)))
