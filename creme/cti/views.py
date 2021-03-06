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

from datetime import timedelta
from functools import partial
# import warnings

from django.db.transaction import atomic
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.html import format_html
from django.utils.timezone import now
from django.utils.translation import gettext as _

from creme.creme_core.auth import build_creation_perm as cperm
from creme.creme_core.auth.decorators import login_required, permission_required
from creme.creme_core.models import CremeEntity, RelationType, Relation
from creme.creme_core.utils import get_from_POST_or_404, get_from_GET_or_404
from creme.creme_core.views import generic
from creme.creme_core.views.bricks import build_context, bricks_render_info
from creme.creme_core.views.decorators import jsonify

from creme import persons, activities

from creme.activities import constants as act_constants
from creme.activities.models import Calendar

from .bricks import CallersBrick

Contact = persons.get_contact_model()
Organisation = persons.get_organisation_model()
Activity = activities.get_activity_model()

RESPOND_TO_A_CALL_MODELS = (Contact, Organisation)  # TODO: move to bricks.py ?


def _create_phonecall(user, title, calltype_id):
    now_value = now()
    return Activity.objects.create(user=user,
                                   title=title,
                                   description=_('Automatically created by CTI'),
                                   status_id=act_constants.STATUS_IN_PROGRESS,
                                   type_id=act_constants.ACTIVITYTYPE_PHONECALL,
                                   sub_type_id=calltype_id,
                                   start=now_value,
                                   end=now_value + timedelta(minutes=5),
                                  )


def abstract_create_phonecall_as_caller(request, pcall_creator=_create_phonecall):
    pcall = _build_related_phonecall(request.user,
                                     get_from_POST_or_404(request.POST, 'entity_id'),
                                     act_constants.ACTIVITYSUBTYPE_PHONECALL_OUTGOING,
                                     _('Call to {entity}'),
                                     pcall_creator=pcall_creator,
                                    )

    return format_html('{msg}<br/><a href="{url}">{pcall}</a>',
                       msg=_('Phone call successfully created.'),
                       url=pcall.get_absolute_url(),
                       pcall=pcall,
                      )


# def abstract_add_contact(request, number,
#                          form=persons.forms.contact.ContactForm,
#                          template='persons/add_contact_form.html',
#                         ):
#     warnings.warn('cti.views.abstract_add_contact() is deprecated ; '
#                   'use the class-based view CTIContactCreation instead.',
#                   DeprecationWarning
#                  )
#     return generic.add_entity(request, form, template=template,
#                               extra_initial={'phone': number},
#                              )


class CTIPersonMixin:
    number_url_kwarg = 'number'

    def get_initial(self):
        initial = super().get_initial()
        initial['phone'] = self.kwargs[self.number_url_kwarg]

        return initial


class CTIContactCreation(CTIPersonMixin, persons.views.contact.ContactCreation):
    pass


# def abstract_add_organisation(request, number,
#                               form=persons.forms.organisation.OrganisationForm,
#                               template='persons/add_organisation_form.html',
#                              ):
#     warnings.warn('cti.views.abstract_add_organisation() is deprecated ; '
#                   'use the class-based view CTIOrganisationCreation instead.',
#                   DeprecationWarning
#                  )
#     return generic.add_entity(request, form, template=template,
#                               extra_initial={'phone': number},
#                              )


class CTIOrganisationCreation(CTIPersonMixin, persons.views.organisation.OrganisationCreation):
    pass


def abstract_add_phonecall(request, entity_id, pcall_creator=_create_phonecall):
    pcall = _build_related_phonecall(request.user, entity_id,
                                     act_constants.ACTIVITYSUBTYPE_PHONECALL_INCOMING,
                                     # _('Call from %s'),
                                     _('Call from {entity}'),
                                     pcall_creator=pcall_creator,
                                    )

    return redirect(pcall)


def _build_related_phonecall(user, entity_id, calltype_id, title_format, pcall_creator=_create_phonecall):
    entity = get_object_or_404(CremeEntity, pk=entity_id)

    user.has_perm_to_link_or_die(entity)
    user.has_perm_to_create_or_die(Activity)

    entity = entity.get_real_entity()
    pcall = pcall_creator(user, title=title_format.format(entity=entity), calltype_id=calltype_id)

    pcall.calendars.add(Calendar.objects.get_default_calendar(user))

    # If the entity is a contact with related user, should add the phone call to his calendar
    if isinstance(entity, Contact) and entity.is_user:
        pcall.calendars.add(Calendar.objects.get_default_calendar(entity.is_user))

    # TODO: link credentials
    caller_rtype = act_constants.REL_SUB_PART_2_ACTIVITY
    entity_rtype = act_constants.REL_SUB_PART_2_ACTIVITY if isinstance(entity, Contact) else \
                   act_constants.REL_SUB_LINKED_2_ACTIVITY
    rtypes_ids   = {caller_rtype, entity_rtype}

    rtypes_map = RelationType.objects.in_bulk(rtypes_ids)
    if len(rtypes_map) != len(rtypes_ids):
        raise Http404('An activities RelationType does not exists !!')

    user_contact = user.linked_contact
    rel_create = partial(Relation.objects.create, object_entity=pcall, user=user)

    if entity.pk != user_contact.pk:
        rel_create(subject_entity=user_contact, type=rtypes_map[caller_rtype])
    rel_create(subject_entity=entity, type=rtypes_map[entity_rtype])

    return pcall


@jsonify
@login_required
@atomic
def create_phonecall_as_caller(request):
    return abstract_create_phonecall_as_caller(request)


class AnswerToACall(generic.BricksView):
    template_name = 'cti/respond_to_a_call.html'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.number = None

    def get_bricks_reload_url(self):
        return reverse('cti__reload_callers_brick', args=(self.get_number(),))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['number'] = self.get_number()

        return context

    def get_number(self):
        number = self.number

        if number is None:
            self.number = number = get_from_GET_or_404(self.request.GET, 'number')

        return number


@login_required
@jsonify
def reload_callers_brick(request, number):
    return bricks_render_info(request, bricks=[CallersBrick()],
                              context=build_context(request, number=number),
                             )


# @login_required
# @permission_required(('persons', cperm(Contact)))
# def add_contact(request, number):
#     warnings.warn('cti.views.add_contact() is deprecated.', DeprecationWarning)
#     return abstract_add_contact(request, number)


# @login_required
# @permission_required(('persons', cperm(Organisation)))
# def add_orga(request, number):
#     warnings.warn('cti.views.add_orga() is deprecated.', DeprecationWarning)
#     return abstract_add_organisation(request, number)


@login_required
@permission_required(('activities', cperm(Activity)))
@atomic
def add_phonecall(request, entity_id):
    return abstract_add_phonecall(request, entity_id)
