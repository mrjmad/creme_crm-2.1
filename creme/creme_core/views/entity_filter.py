# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2009-2019  Hybird
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
################################################################################

import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.db.models.deletion import ProtectedError
from django.http import Http404  # HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext_lazy as _, gettext

from .. import utils
from ..auth.decorators import login_required
from ..core.entity_filter import entity_filter_registries, EF_USER
from ..core.exceptions import ConflictError
from ..forms.entity_filter import forms as efilter_forms
from ..gui.listview import ListViewState
from ..http import CremeJsonResponse
from ..models import EntityFilter, RelationType
from ..utils import (
    get_from_GET_or_404,
    db as db_utils,
)
from ..utils.unicode_collation import collator

from . import generic
from .decorators import jsonify
from .generic import base

logger = logging.getLogger(__name__)
User = get_user_model()


class FilterMixin:
    """Code factorisation with HeaderFilter views."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lv_url = None

    def build_lv_url(self):
        url = self.lv_url

        if url is None:
            url = self.request.POST.get('cancel_url')

            if not url:
                model = self.object.entity_type.model_class()

                try:
                    url = model.get_lv_absolute_url()
                except AttributeError:
                    logger.debug('"%s" has no get_lv_absolute_url() method ?!', model)
                    url = ''

            self.lv_url = url

        return url

    def check_filter_permissions(self, filter_obj, user):
        allowed, msg = filter_obj.can_edit(user)

        if not allowed:
            raise PermissionDenied(msg)

    @staticmethod
    def get_case_sensitivity_message():
        if not db_utils.is_db_equal_case_sensitive():
            if not db_utils.is_db_like_case_sensitive():
                return _('Notice: your database is not case sensitive, so the string operators '
                         'which are case sensitive and the ones which are not will accept the same entities.'
                        )

            return _('Notice: your database is not case sensitive for the "equals" operator, '
                     'so the string equality operators which are case sensitive and the ones '
                     'which are not will accept the same entities.'
                    )
        elif not db_utils.is_db_like_case_sensitive():
            return _('Notice: your database is not case sensitive, so the string operators '
                     'which are case sensitive and the ones which are not will accept the same entities '
                     '(excepted equality ones, which are case sensitive).'
                    )

        return None

    def get_success_url(self):
        return self.build_lv_url() or reverse('creme_core__home')

    def save_in_session(self, lvs_attr):
        request = self.request
        lv_url = self.build_lv_url()
        lvs = ListViewState.get_state(request, lv_url) or \
              ListViewState(url=lv_url)

        setattr(lvs, lvs_attr, self.object.id)
        lvs.register_in_session(request)


# class FilterCreationMixin(base.EntityCTypeRelatedMixin, FilterMixin):
#     ctype_form_kwarg = 'ctype'
#
#     def get_form_kwargs(self):
#         kwargs = super().get_form_kwargs()
#         kwargs[self.ctype_form_kwarg] = self.get_ctype()
#
#         return kwargs
#
#     def save_in_session(self, lvs_attr):
#         request = self.request
#         lv_url = self.build_lv_url()
#         lvs = ListViewState.get_state(request, lv_url) or \
#               ListViewState(url=lv_url)
#
#         setattr(lvs, lvs_attr, self.object.id)
#         lvs.register_in_session(request)


# class FilterEditionMixin(FilterMixin):
#     def get_object(self, *args, **kwargs):
#         filter_ = super().get_object(*args, **kwargs)
#
#         allowed, msg = filter_.can_edit(self.request.user)
#         if not allowed:
#             raise PermissionDenied(msg)
#
#         return filter_
class EntityFilterMixin(FilterMixin):
    efilter_registry = entity_filter_registries[EF_USER]

    def get_efilter_registry(self):
        return self.efilter_registry


# class EntityFilterCreation(FilterCreationMixin, generic.CremeModelCreation):
class EntityFilterCreation(base.EntityCTypeRelatedMixin,
                           EntityFilterMixin,
                           generic.CremeModelCreation):
    model = EntityFilter
    form_class = efilter_forms.EntityFilterCreateForm
    template_name = 'creme_core/forms/entity-filter.html'
    ctype_form_kwarg = 'ctype'

    def form_valid(self, form):
        response = super().form_valid(form)
        self.save_in_session('entity_filter_id')

        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['help_message'] = self.get_case_sensitivity_message()

        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs[self.ctype_form_kwarg] = self.get_ctype()
        kwargs['efilter_registry'] = self.get_efilter_registry()

        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        initial['is_private'] = settings.FILTERS_INITIAL_PRIVATE

        return initial


# class EntityFilterEdition(FilterEditionMixin, generic.CremeModelEdition):
class EntityFilterEdition(EntityFilterMixin, generic.CremeModelEdition):
    model = EntityFilter
    form_class = efilter_forms.EntityFilterEditForm
    template_name = 'creme_core/forms/entity-filter.html'
    pk_url_kwarg = 'efilter_id'
    submit_label = _('Save the modified filter')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['help_message'] = self.get_case_sensitivity_message()

        return context

    def get_object(self, *args, **kwargs):
        efilter = super().get_object(*args, **kwargs)
        self.check_filter_permissions(filter_obj=efilter, user=self.request.user)

        return efilter

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['efilter_registry'] = self.get_efilter_registry()

        return kwargs


# @login_required
# def delete(request):
#     efilter      = get_object_or_404(EntityFilter, pk=utils.get_from_POST_or_404(request.POST, 'id'))
#     callback_url = efilter.entity_type.model_class().get_lv_absolute_url()
#     allowed, msg = efilter.can_delete(request.user)
#     status = 400  # todo: 409 ??
#
#     if allowed:
#         try:
#             efilter.delete()
#         except EntityFilter.DependenciesError as e:
#             return_msg = str(e)
#         except ProtectedError as e:
#             return_msg = gettext('«{}» can not be deleted because of its dependencies.').format(efilter)
#             return_msg += render_to_string('creme_core/templatetags/widgets/list_instances.html',
#                                            {'objects': e.args[1][:25], 'user': request.user},
#                                            request=request,
#                                           )
#         else:
#             return_msg = gettext('Filter successfully deleted')
#             status = 200
#     else:
#         return_msg = msg
#
#     if request.is_ajax():
#         return HttpResponse(return_msg, status=status)
#
#     return HttpResponseRedirect(callback_url)
class EntityFilterDeletion(generic.CremeModelDeletion):
    model = EntityFilter

    def check_instance_permissions(self, instance, user):
        allowed, msg = instance.can_delete(user)
        if not allowed:
            raise PermissionDenied(msg)

    def get_success_url(self):
        return self.object.entity_type.model_class().get_lv_absolute_url()

    def perform_deletion(self, request):
        try:
            super().perform_deletion(request)
        except EntityFilter.DependenciesError as e:
            raise ConflictError(e) from e
        # TODO: move in a middleware ??
        except ProtectedError as e:
            msg = gettext('The filter can not be deleted because of its dependencies.')
            msg += render_to_string(
                'creme_core/templatetags/widgets/list_instances.html',
                {'objects': e.args[1][:25], 'user': request.user},
                request=request,
            )
            raise ConflictError(msg) from e


# TODO: factorise with views.relations.json_rtype_ctypes  ???
@login_required
@jsonify
def get_content_types(request, rtype_id):
    content_types = get_object_or_404(RelationType, pk=rtype_id).object_ctypes.all() or \
                    utils.creme_entity_content_types()

    return [
        (0, gettext('All')),
        *((ct.id, str(ct)) for ct in content_types),
    ]


# @login_required
# @jsonify
# def get_for_ctype(request):
#     GET = request.GET
#     ct_id = utils.get_from_GET_or_404(GET, 'ct_id', int)
#     include_all = utils.get_from_GET_or_404(GET, 'all', cast=utils.bool_from_str_extended, default='0')
#     ct = utils.get_ct_or_404(ct_id)
#     user = request.user
#
#     user.has_perm_to_access_or_die(ct.app_label)
#
#     choices = [('', ugettext('All'))] if include_all else []
#     choices.extend(EntityFilter.get_for_user(user, ct).values_list('id', 'name'))
#
#     return choices
class EntityFilterChoices(base.ContentTypeRelatedMixin, base.CheckedView):
    response_class = CremeJsonResponse
    ctype_id_arg = 'ct_id'
    include_all_arg = 'all'
    all_label = _('All')  # TODO: pgettext_lazy (in other places too)

    def check_related_ctype(self, ctype):
        self.request.user.has_perm_to_access_or_die(ctype.app_label)

    def get_ctype_id(self):
        return utils.get_from_GET_or_404(self.request.GET, self.ctype_id_arg, int)

    def get_include_all(self):
        return utils.get_from_GET_or_404(self.request.GET,
                                         key=self.include_all_arg,
                                         cast=utils.bool_from_str_extended,
                                         default='0',
                                        )

    def get_choices(self):
        choices = [('', self.all_label)] if self.get_include_all() else []
        choices.extend(EntityFilter.get_for_user(self.request.user, self.get_ctype())
                                   .values_list('id', 'name')
                      )

        return choices

    def get(self, request, *args, **kwargs):
        return self.response_class(
            self.get_choices(),
            safe=False,  # Result is not a dictionary
        )


# TODO: generalize this view to all enumerable models (inherit enumerable view ?)
#       anyway, we need other examples of operand...
class UserChoicesView(base.CheckedView):
    response_class = CremeJsonResponse
    filter_type_arg = 'filter_type'

    def get_registry(self):
        ftype = get_from_GET_or_404(
            self.request.GET, key=self.filter_type_arg, cast=int,
            default=EF_USER,  # TODO: make mandatory ?
        )

        try:
            return entity_filter_registries[ftype]
        except KeyError as e:
            raise Http404('Invalid filter type') from e

    def get_operands(self):
        user = self.request.user

        for operand in self.get_registry().operands(user):
            if issubclass(operand.model, User):
                yield operand

    def get(self, request, *args, **kwargs):
        sort_key = collator.sort_key

        def choice_key(c):
            return sort_key(c[1])

        # TODO: return group for teams & inactive users (see UserEnumerator)
        #       => fix the JavaScript side (it concatenates the group label at the end)
        return self.response_class(
            [*sorted(((op.type_id, op.verbose_name) for op in self.get_operands()),
                     key=choice_key,
                    ),
             *sorted(((e.id, str(e)) for e in User.objects.all()),
                     key=choice_key,
                    )
            ],
            safe=False,  # Result is not a dictionary
        )
