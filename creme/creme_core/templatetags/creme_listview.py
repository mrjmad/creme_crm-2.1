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

from collections import defaultdict
import logging

from django.contrib.auth import get_user_model
# from django.conf import settings
# from django.db.models import ForeignKey, ManyToManyField, BooleanField, DateField
from django.template import Library
from django.template.loader import get_template
# from django.utils.translation import ugettext as _

# from ..core.entity_cell import (EntityCellRegularField, EntityCellCustomField,
#         EntityCellFunctionField, EntityCellRelation)
# from ..core.enumerable import enumerable_registry, Enumerator
from ..core.paginator import FlowPaginator
from ..gui.bulk_update import bulk_update_registry
# from ..gui.listview import NULL_FK
from ..gui.pager import PagerContext
# from ..models import CustomField
from ..utils.unicode_collation import collator

logger = logging.getLogger(__name__)
register = Library()


# @register.inclusion_tag('creme_core/templatetags/entity-filters.html', takes_context=True)
# def get_listview_entity_filters(context):
#     efilter = context['entity_filters'].selected
#
#     if efilter:
#         efilter_id = efilter.id
#         user = context['user']
#         can_edit   = efilter.can_edit(user)[0]
#         can_delete = efilter.can_delete(user)[0]
#     else:
#         efilter_id = 0
#         can_edit = can_delete = False
#
#     context['efilter_id'] = efilter_id
#     context['can_edit'] = can_edit
#     context['can_delete'] = can_delete
#
#     return context
@register.inclusion_tag('creme_core/templatetags/listview/entity-filters.html')
def listview_entity_filters(*, model, user, efilters, show_buttons):
    efilter = efilters.selected

    if efilter:
        efilter_id = efilter.id
        can_edit   = efilter.can_edit(user)[0]
        can_delete = efilter.can_delete(user)[0]
    else:
        efilter_id = 0
        can_edit = can_delete = False

    return {
        'user': user,
        'model': model,
        'entity_filters': efilters,
        'efilter_id': efilter_id,
        'can_edit': can_edit,
        'can_delete': can_delete,
        'show_buttons': show_buttons,
    }


# @register.inclusion_tag('creme_core/templatetags/header-filters.html', takes_context=True)
# def get_listview_headerfilters(context):
#     hfilter = context['header_filters'].selected
#     user = context['user']
#
#     context['hfilter_id'] = hfilter.id
#     context['can_edit']   = hfilter.can_edit(user)[0]
#     context['can_delete'] = hfilter.can_delete(user)[0]
#
#     return context
@register.inclusion_tag('creme_core/templatetags/listview/header-filters.html')
def listview_header_filters(*, model, user, hfilters, show_buttons):
    selected_hfilter = hfilters.selected

    grouped_hfilters = defaultdict(list)
    for hfilter in hfilters:
        grouped_hfilters[hfilter.user_id].append(hfilter)

    global_header_filters = grouped_hfilters.pop(None, ())
    my_header_filters     = grouped_hfilters.pop(user.id, ())

    if grouped_hfilters:
        users = get_user_model().objects.in_bulk(grouped_hfilters.keys())
        other_header_filters = [
            (users.get(user_id), user_hfilters)
                for user_id, user_hfilters in grouped_hfilters.items()
        ]

        sort_key = collator.sort_key
        other_header_filters.sort(key=lambda t: sort_key(str(t[0])))
    else:
        other_header_filters = ()

    return {
        'model': model,
        # 'header_filters': hfilters,

        'global_header_filters': global_header_filters,
        'my_header_filters':     my_header_filters,
        'other_header_filters':  other_header_filters,

        'selected': selected_hfilter,
        # 'hfilter_id': selected_hfilter.id,

        'can_edit':   selected_hfilter.can_edit(user)[0],
        'can_delete': selected_hfilter.can_delete(user)[0],

        'show_buttons': show_buttons,
    }


class PagerRenderer:
    template_name = ''

    def render(self, page):
        return get_template(self.template_name).render(self.get_context(page))

    def get_context(self, page):
        return {'page': page}


class FlowPagerRenderer(PagerRenderer):
    template_name = 'creme_core/templatetags/listview/paginator-fast.html'


class DefaultPagerRenderer(PagerRenderer):
    template_name = 'creme_core/templatetags/listview/paginator-slow.html'

    def get_context(self, page):
        return {'pager': PagerContext(page)}


PAGINATOR_RENDERERS = {
    FlowPaginator: FlowPagerRenderer,
}


@register.simple_tag
def listview_pager(page):
    renderer_class = PAGINATOR_RENDERERS.get(page.paginator.__class__, DefaultPagerRenderer)
    return renderer_class().render(page)


# def _build_bool_search_widget(widget_ctx, search_value):
#     selected_value = search_value[0] if search_value else None
#     widget_ctx['type'] = 'checkbox'
#     widget_ctx['values'] = [{'value':    '1',
#                              'text':     _('Yes'),
#                              'selected': 'selected' if selected_value == '1' else ''
#                             },
#                             {'value':    '0',
#                              'text':     _('No'),
#                              'selected': 'selected' if selected_value == '0' else ''
#                             }
#                            ]


# def _build_date_search_widget(widget_ctx, search_value):
#     widget_ctx['type'] = 'datefield'
#
#     date_format = settings.DATE_FORMAT_JS.get(settings.DATE_FORMAT)
#     if date_format:
#         widget_ctx['format'] = date_format
#
#     if search_value:
#         widget_ctx['values'] = {'start': search_value[0], 'end': search_value[-1]}


# def _build_select_search_widget(widget_ctx, search_value, choices):
#     selected_value = search_value[0] if search_value else None  # meh
#     widget_ctx['type'] = 'select'
#     groups = defaultdict(list)
#
#     for choice in choices:
#         value = str(choice['value'])
#         groups[choice.get('group')].append(
#             {'value': value,
#              'text': choice['label'],
#              'selected': selected_value == value,
#             }
#         )
#
#     widget_ctx['values'] = list(groups.items())


# @register.inclusion_tag('creme_core/templatetags/listview_columns_header.html', takes_context=True)
# def get_listview_columns_header(context):
#     header_searches = dict(context['list_view_state'].research)
#
#     for cell in context['cells']:
#         if not cell.has_a_filter:
#             continue
#
#         search_value = header_searches.get(cell.key, '')
#         widget_ctx = {'value': search_value, 'type': 'text'}
#
#         if isinstance(cell, EntityCellRegularField):
#             field = cell.field_info[-1]
#
#             if isinstance(field, (ForeignKey, ManyToManyField)):
#                 if cell.filter_string.endswith('__header_filter_search_field__icontains'):
#                     if search_value:
#                         widget_ctx['value'] = search_value[0]
#                 else:
#                     try:
#                         enumerator = enumerable_registry.enumerator_by_field(field)
#                     except ValueError:
#                         continue
#                     else:
#                         choices = enumerator.choices(context['user'])
#
#                         if field.null or field.many_to_many:
#                             choices.insert(0, {'value': NULL_FK, 'label': _('* is empty *')})
#
#                         _build_select_search_widget(widget_ctx, search_value, choices)
#             elif field.choices:
#                 _build_select_search_widget(widget_ctx, search_value,
#                                             Enumerator.convert_choices(field.choices)
#                                            )
#             elif isinstance(field, BooleanField):
#                 _build_bool_search_widget(widget_ctx, search_value)
#             elif isinstance(field, DateField):
#                 _build_date_search_widget(widget_ctx, search_value)
#             elif search_value:
#                 widget_ctx['value'] = search_value[0]
#         elif isinstance(cell, EntityCellFunctionField):
#             choices = cell.function_field.choices
#             if choices is not None:
#                 _build_select_search_widget(widget_ctx, search_value,
#                                             Enumerator.convert_choices(choices)
#                                            )
#             elif search_value:
#                 widget_ctx['value'] = search_value[0]
#         elif isinstance(cell, EntityCellRelation):
#             if search_value:
#                 widget_ctx['value'] = search_value[0]
#         elif isinstance(cell, EntityCellCustomField):
#             cf = cell.custom_field
#             field_type = cf.field_type
#
#             if field_type in (CustomField.ENUM, CustomField.MULTI_ENUM):
#                 choices = [{'value': NULL_FK, 'label': _('* is empty *')}]
#                 choices.extend(Enumerator.convert_choices(cf.customfieldenumvalue_set.values_list('id', 'value')))
#
#                 _build_select_search_widget(widget_ctx, search_value, choices)
#             elif field_type == CustomField.DATETIME:
#                 _build_date_search_widget(widget_ctx, search_value)
#             elif field_type == CustomField.BOOL:
#                 _build_bool_search_widget(widget_ctx, search_value)
#             elif search_value:
#                 widget_ctx['value'] = search_value[0]
#
#         cell.widget_ctx = widget_ctx
#
#     context['NULL_FK'] = NULL_FK
#
#     return context


@register.inclusion_tag('creme_core/templatetags/listview/buttons.html', takes_context=True)
def listview_buttons(context, *, model, buttons):
    request = context['request']  # TODO: argument ?

    return {
        'request': request,
        'user': request.user,
        'model': model,
        'list_view_state': context['list_view_state'],
        'buttons': ((button, button.get_context(request=request, lv_context=context))
                        for button in buttons.instances
                   ),
    }


@register.simple_tag
# def listview_header_colspan(cells, is_readonly, is_single_select):
def listview_header_colspan(*, cells, is_readonly, is_single_select):
    colspan = len(cells) if is_readonly else \
              sum(2 if cell.type_id != 'actions' else 1 for cell in cells)

    return colspan if is_single_select else colspan + 1


@register.filter('listview_column_colspan')
def get_column_colspan(cell, is_readonly):
    return 2 if cell.type_id != 'actions' and not is_readonly else 1


@register.inclusion_tag('creme_core/templatetags/listview/td-action.html')
# def listview_td_action_for_cell(cell, instance, user):
def listview_td_action_for_cell(*, cell, instance, user):
    from creme.creme_core.views.entity import _bulk_has_perm

    return {
        # TODO: pass the registry in a list-view context
        'edit_url':  bulk_update_registry.inner_uri(cell=cell, instance=instance, user=user),
        'edit_perm': _bulk_has_perm(instance, user),
    }


@register.inclusion_tag('creme_core/templatetags/listview/entity-actions.html')
# def listview_entity_actions(cell, instance, user):
def listview_entity_actions(*, cell, instance, user):
    actions = cell.instance_actions(instance=instance, user=user)
    count = len(actions)

    return {
        'id': instance.id,
        'actions': {
            'default': actions[0] if count > 0 else None,
            'others': actions[1:] if count > 1 else [],
        },
    }


@register.inclusion_tag('creme_core/templatetags/listview/header-actions.html')
# def listview_header_actions(cell, user):
def listview_header_actions(*, cell, user):
    return {
        'actions': cell.bulk_actions(user),
    }
