# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2009-2015  Hybird
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

from django.core.urlresolvers import reverse_lazy as reverse
from django.utils.translation import ugettext_lazy as _

from creme.creme_core.auth import build_creation_perm
from creme.creme_core.core.setting_key import setting_key_registry
from creme.creme_core.gui import (creme_menu, block_registry, button_registry,
        icon_registry, bulk_update_registry, import_form_registry, smart_columns_registry)
from creme.creme_core.registry import creme_registry

from . import get_activity_model
from .blocks import block_list
from .buttons import add_activity_button, add_meeting_button, add_phonecall_button, add_task_button
from .constants import REL_OBJ_PART_2_ACTIVITY, REL_OBJ_ACTIVITY_SUBJECT
from .forms.activity_type import BulkEditTypeForm
from .forms.lv_import import get_csv_form_builder
#from .models import Activity
from .setting_keys import review_key, auto_subjects_key


Activity = get_activity_model()

creme_registry.register_app('activities', _(u'Activities'), '/activities')
creme_registry.register_entity_models(Activity)

creation_perm = build_creation_perm(Activity)
reg_item = creme_menu.register_app('activities', '/activities/').register_item
reg_item('/activities/',                       _(u"Portal of activities"),   'activities')
reg_item('/activities/calendar/user',          _(u'Calendar'),               'activities')
#reg_item('/activities/activity/add',           Activity.creation_label,      'activities.add_activity')
#reg_item('/activities/activity/add/meeting',   _(u'Add a meeting'),          'activities.add_activity')
#reg_item('/activities/activity/add/phonecall', _(u'Add a phone call'),       'activities.add_activity')
#reg_item('/activities/activity/add/task',      _(u'Add a task'),             'activities.add_activity')
#reg_item('/activities/activity/add_indispo',   _(u'Add an indisponibility'), 'activities.add_activity')
#reg_item('/activities/activities',             _(u'All activities'),         'activities')
#reg_item('/activities/phone_calls',            _(u'All phone calls'),        'activities')
#reg_item('/activities/meetings',               _(u'All meetings'),           'activities')
reg_item(reverse('activities__create_activity'),                      Activity.creation_label, creation_perm)
reg_item(reverse('activities__create_activity', args=('meeting',)),   _(u'Add a meeting'),     creation_perm)
reg_item(reverse('activities__create_activity', args=('phonecall',)), _(u'Add a phone call'),  creation_perm)
reg_item(reverse('activities__create_activity', args=('task',)),      _(u'Add a task'),        creation_perm)
reg_item(reverse('activities__create_indispo'),   _(u'Add an indisponibility'), creation_perm)
reg_item(reverse('activities__list_activities'),  _(u'All activities'),         'activities')
reg_item(reverse('activities__list_phone_calls'), _(u'All phone calls'),        'activities')
reg_item(reverse('activities__list_meetings'),    _(u'All meetings'),           'activities')

block_registry.register(*block_list)

button_registry.register(add_activity_button, add_meeting_button, add_phonecall_button, add_task_button)

icon_registry.register(Activity, 'images/calendar_%(size)s.png')

bulk_update_registry.register(Activity, exclude=('start', 'end', 'busy', 'is_all_day'),
                              innerforms={'type':     BulkEditTypeForm,
                                          'sub_type': BulkEditTypeForm,
                                         }
                             )

import_form_registry.register(Activity, get_csv_form_builder)

smart_columns_registry.register_model(Activity).register_field('title') \
                                               .register_field('start') \
                                               .register_relationtype(REL_OBJ_PART_2_ACTIVITY) \
                                               .register_relationtype(REL_OBJ_ACTIVITY_SUBJECT)

setting_key_registry.register(review_key, auto_subjects_key)
