# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
from collections import OrderedDict

from django.contrib import admin as djangoadmin, messages
from django.contrib.admin import helpers as djangohelpers
from django.contrib.admin.utils import model_ngettext
from django.contrib.admin.views import main
from django.core.exceptions import PermissionDenied
from django.forms import ALL_FIELDS
from django.forms.models import modelform_defines_fields
from django.http import HttpResponseRedirect
from django.template.response import SimpleTemplateResponse, TemplateResponse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _, ngettext
from django.views.decorators.csrf import csrf_protect

from ..forms import ModelForm, modelform_factory
from .views import ChangeList


csrf_protect_m = method_decorator(csrf_protect)


class ModelAdmin(djangoadmin.ModelAdmin):

    form = ModelForm

    def get_queryset(self, request):
        return getattr(self.model, "objects", None) or self.session.query(self.model)

    def get_object(self, request, object_id, from_field=None):
        q = getattr(self.model, "objects", None) or self.session.query(self.model)
        return q.get(object_id)

    def get_changelist(self, request):
        """
        Return a `ChangeList` instance based on `request`. May raise
        `IncorrectLookupParameters`.
        """
        return ChangeList

    @csrf_protect_m
    def changelist_view(self, request, extra_context=None):
        """
        The 'change list' admin view for this model.
        """
        opts = self.model._meta
        app_label = opts.app_label
        if not self.has_view_or_change_permission(request):
            raise PermissionDenied

        try:
            cl = self.get_changelist_instance(request)
        except djangoadmin.views.main.IncorrectLookupParameters:
            # Wacky lookup parameters were given, so redirect to the main
            # changelist page, without parameters, and pass an 'invalid=1'
            # parameter via the query string. If wacky parameters were given
            # and the 'invalid=1' parameter was already in the query string,
            # something is screwed up with the database, so display an error
            # page.
            if main.ERROR_FLAG in request.GET:
                return SimpleTemplateResponse("admin/invalid_setup.html", {"title": _("Database error")})
            return HttpResponseRedirect(request.path + "?" + main.ERROR_FLAG + "=1")

        # If the request was POSTed, this might be a bulk action or a bulk
        # edit. Try to look up an action or confirmation first, but if this
        # isn't an action the POST will fall through to the bulk edit check,
        # below.
        action_failed = False
        selected = request.POST.getlist(djangohelpers.ACTION_CHECKBOX_NAME)

        actions = self.get_actions(request)
        # Actions with no confirmation
        if actions and request.method == "POST" and "index" in request.POST and "_save" not in request.POST:
            if selected:
                response = self.response_action(request, queryset=cl.get_queryset(request))
                if response:
                    return response
                else:
                    action_failed = True
            else:
                msg = _("Items must be selected in order to perform " "actions on them. No items have been changed.")
                self.message_user(request, msg, messages.WARNING)
                action_failed = True

        # Actions with confirmation
        if (
            actions
            and request.method == "POST"
            and djangohelpers.ACTION_CHECKBOX_NAME in request.POST
            and "index" not in request.POST
            and "_save" not in request.POST
        ):
            if selected:
                response = self.response_action(request, queryset=cl.get_queryset(request))
                if response:
                    return response
                else:
                    action_failed = True

        if action_failed:
            # Redirect back to the changelist page to avoid resubmitting the
            # form if the user refreshes the browser or uses the "No, take
            # me back" button on the action confirmation page.
            return HttpResponseRedirect(request.get_full_path())

        # If we're allowing changelist editing, we need to construct a formset
        # for the changelist given all the fields to be edited. Then we'll
        # use the formset to validate/process POSTed data.
        formset = cl.formset = None

        # Handle POSTed bulk-edit data.
        if request.method == "POST" and cl.list_editable and "_save" in request.POST:
            if not self.has_change_permission(request):
                raise PermissionDenied
            FormSet = self.get_changelist_formset(request)
            modified_objects = self._get_list_editable_queryset(request, FormSet.get_default_prefix())
            formset = cl.formset = FormSet(request.POST, request.FILES, queryset=modified_objects)
            if formset.is_valid():
                changecount = 0
                for form in formset.forms:
                    if form.has_changed():
                        obj = self.save_form(request, form, change=True)
                        self.save_model(request, obj, form, change=True)
                        self.save_related(request, form, formsets=[], change=True)
                        change_msg = self.construct_change_message(request, form, None)
                        self.log_change(request, obj, change_msg)
                        changecount += 1

                if changecount:
                    msg = ngettext(
                        "%(count)s %(name)s was changed successfully.",
                        "%(count)s %(name)s were changed successfully.",
                        changecount,
                    ) % {"count": changecount, "name": model_ngettext(opts, changecount)}
                    self.message_user(request, msg, messages.SUCCESS)

                return HttpResponseRedirect(request.get_full_path())

        # Handle GET -- construct a formset for display.
        elif cl.list_editable and self.has_change_permission(request):
            FormSet = self.get_changelist_formset(request)
            formset = cl.formset = FormSet(queryset=cl.result_list)

        # Build the list of media to be used by the formset.
        if formset:
            media = self.media + formset.media
        else:
            media = self.media

        # Build the action form and populate it with available actions.
        if actions:
            action_form = self.action_form(auto_id=None)
            action_form.fields["action"].choices = self.get_action_choices(request)
            media += action_form.media
        else:
            action_form = None

        selection_note_all = ngettext("%(total_count)s selected", "All %(total_count)s selected", cl.result_count)

        context = {
            **self.admin_site.each_context(request),
            "module_name": str(opts.verbose_name_plural),
            "selection_note": _("0 of %(cnt)s selected") % {"cnt": cl.result_list.count()},
            "selection_note_all": selection_note_all % {"total_count": cl.result_count},
            "title": cl.title,
            "is_popup": cl.is_popup,
            "to_field": cl.to_field,
            "cl": cl,
            "media": media,
            "has_add_permission": self.has_add_permission(request),
            "opts": cl.opts,
            "action_form": action_form,
            "actions_on_top": self.actions_on_top,
            "actions_on_bottom": self.actions_on_bottom,
            "actions_selection_counter": self.actions_selection_counter,
            "preserved_filters": self.get_preserved_filters(request),
            **(extra_context or {}),
        }

        request.current_app = self.admin_site.name

        return TemplateResponse(
            request,
            self.change_list_template
            or [
                "admin/%s/%s/change_list.html" % (app_label, opts.model_name),
                "admin/%s/change_list.html" % app_label,
                "admin/change_list.html",
            ],
            context,
        )

    def get_form(self, request, obj=None, change=False, **kwargs):

        fields = kwargs.pop("fields", None)
        excluded = self.get_exclude(request, obj)
        exclude = [] if excluded is None else list(excluded)
        readonly_fields = self.get_readonly_fields(request, obj)
        exclude.extend(readonly_fields)
        if change and hasattr(request, "user") and not self.has_change_permission(request, obj):
            exclude.extend(fields)
        if excluded is None and hasattr(self.form, "_meta") and self.form._meta.exclude:
            # Take the custom ModelForm's Meta.exclude into account only if the
            # ModelAdmin doesn't define its own.
            exclude.extend(self.form._meta.exclude)
        # if exclude is an empty list we pass None to be consistent with the
        # default on modelform_factory
        exclude = exclude or None

        # Remove declared form fields which are in readonly_fields.
        new_attrs = OrderedDict.fromkeys(f for f in readonly_fields if f in self.form.declared_fields)
        new_attrs["__module__"] = self.form.__module__
        form = type(self.form.__name__, (self.form,), new_attrs)
        defaults = {"form": form, "fields": fields, "exclude": exclude, "session": self.session, **kwargs}

        if defaults["fields"] is None and not modelform_defines_fields(defaults["form"]):
            defaults["fields"] = ALL_FIELDS

        return modelform_factory(self.model, **defaults)

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        pass

    def save_model(self, request, obj, form, change):
        """
        Given a model instance save it to the database.
        """
        if obj not in self.session:
            self.session.add(obj)


def admin_factory(model, session=None, options=None):
    """
    Generates a ModelAdmin class for a sqlalchemy model
    """
    options = options or {}
    # TODO: fill this in
    options["__module__"] = __name__
    options["session"] = session or model.objects.session
    return type(str(model.__name__ + "Admin"), (ModelAdmin,), options)
