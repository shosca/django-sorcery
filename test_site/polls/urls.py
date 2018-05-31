# -*- coding: utf-8 -*-
from django.urls import path, include

from django_sorcery.routers import SimpleRouter

from . import views

router = SimpleRouter()
router.register("", views.PollsViewSet)

app_name = "polls"
urlpatterns = [path("", include(router.urls))]
