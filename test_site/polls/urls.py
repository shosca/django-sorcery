# -*- coding: utf-8 -*-
from django.urls import path, include

from django_sorcery.routers import SimpleRouter

from . import views

router = SimpleRouter()
router.register("polls", views.PollsViewSet)


app_name = "polls"
urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("<int:pk>/", views.DetailView.as_view(), name="detail"),
    path("<int:pk>/results", views.ResultsView.as_view(), name="results"),
    path("<int:question_id>/vote", views.vote, name="vote"),
    path("v/", include(router.urls)),
]
