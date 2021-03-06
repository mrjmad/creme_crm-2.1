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

# from collections import defaultdict
# from functools import partial
import logging

# from django.db.models import Q, DateField, ForeignKey, ManyToManyField
# from django.utils.encoding import smart_str
# from django.utils.timezone import now

# from creme.creme_core.core.entity_cell import (EntityCellRegularField, EntityCellCustomField,
#         EntityCellFunctionField, EntityCellRelation)
# from creme.creme_core.core.entity_cell import EntityCellRegularField
# from creme.creme_core.models import Relation, CustomField
# from creme.creme_core.utils import find_first
# from creme.creme_core.utils.date_range import CustomRange
# from creme.creme_core.utils.dates import dt_from_str
# from creme.creme_core.utils.db import get_indexed_ordering
from creme.creme_core.utils.queries import QSerializer

# NULL_FK = 'NULL'
logger = logging.getLogger(__name__)


class NoHeaderFilterAvailable(Exception):
    pass


# def simple_value(value):
#     if value:
#         if hasattr(value, '__iter__') and len(value) == 1:
#             return value[0]
#         return value
#     return ''


class ListViewState:
    # class _OrderedField:
    #     def __init__(self, ord_field_str):
    #         "@param ord_field_str: something like 'name' or '-creation_date'"
    #         self._raw = ord_field_str
    #
    #         if ord_field_str.startswith('-'):
    #             self.field_name = ord_field_str[1:]
    #             self.order = '-'
    #         else:
    #             self.field_name = ord_field_str
    #             self.order = ''
    #
    #     def __str__(self):
    #         return self._raw
    #
    #     def reverse(self):
    #         "Returns the _OrderedField instance corresponding to the same field but with reversed order."
    #         return self.__class__(self.field_name if self.order else '-' + self.field_name)

    def __init__(self, **kwargs):
        get_arg = kwargs.get
        self.entity_filter_id = get_arg('filter')
        self.header_filter_id = get_arg('hfilter')
        self.page = get_arg('page')
        self.rows = get_arg('rows')
        self.sort_order = get_arg('sort_order')
        # self.sort_field = get_arg('sort_field')
        self.sort_cell_key = get_arg('sort_cell_key')
        self.url = get_arg('url')
        # self.research = ()
        self.search = {}
        self.extra_q = None

    def __repr__(self):
        return ('<ListViewState(efilter_id={efilter}, hfilter_id={hfilter}, page={page},'
                # ' rows={rows}, sort={sortorder}{sortfield}, url={url},'
                ' rows={rows}, sort={sortorder}{sortkey}, url={url},'
                # ' research={research}, extra_q={extra_q})>'.format(
                ' search={search}, extra_q={extra_q})>'.format(
            efilter=self.entity_filter_id,
            hfilter=self.header_filter_id,
            page=self.page, rows=self.rows,
            # sortorder=self.sort_order, sortfield=self.sort_field,
            sortorder=self.sort_order, sortkey=self.sort_cell_key,
            url=self.url,
            # research=self.research,
            search=self.search,
            extra_q=self.extra_q,
        ))

    def register_in_session(self, request):
        serialized = {**self.__dict__}

        if self.extra_q is not None:
            serialized['extra_q'] = QSerializer().dumps(self.extra_q)

        request.session[self.url] = serialized

    # @staticmethod
    @classmethod
    # def get_state(request, url=None):
    def get_state(cls, request, url=None):
        lvs = None
        data = request.session.get(url or request.path)

        if data is not None:
            # # lvs = object.__new__(ListViewState)  # NB: causes problem on attribute change (renaming...)
            # lvs = ListViewState()
            lvs = cls()

            for k, v in data.items():
                setattr(lvs, k, v)

            if lvs.extra_q is not None:
                lvs.extra_q = QSerializer().loads(lvs.extra_q)

        return lvs

    # @staticmethod
    @classmethod
    # def build_from_request(arguments, url, **kwargs):
    def build_from_request(cls, arguments, url, **kwargs):
        kwargs.update((str(k), v) for k, v in arguments.items())
        kwargs['url'] = url

        # return ListViewState(**kwargs)
        return cls(**kwargs)

    # @staticmethod
    @classmethod
    # def get_or_create_state(request, url, **kwargs):
    def get_or_create_state(cls, request, url, **kwargs):
        # state = ListViewState.get_state(request, url)
        state = cls.get_state(request, url)

        if state is None:
            arguments = request.POST if request.method == 'POST' else request.GET
            # state = ListViewState.build_from_request(arguments, url, **kwargs)
            state = cls.build_from_request(arguments, url, **kwargs)

        return state

    # def clear_research(self):
    #     self.research = ()

    # def handle_research(self, arguments, cells, merge=False):
    #     "Handle strings to use in order to filter (strings are in the request)."
    #     list_session = list(self.research) if merge else []
    #     getlist = arguments.getlist
    #
    #     for cell in cells:
    #         if cell.has_a_filter:
    #             cell_key = cell.key
    #             values = getlist(cell_key)
    #
    #             if values:
    #                 filtered_attr = [smart_str(value.strip()) for value in values]
    #
    #                 if filtered_attr and any(filtered_attr):
    #                     list_session.append((cell_key, filtered_attr))
    #
    #     self.research = list_session

    def set_headerfilter(self, header_filters, id=-1, default_id=''):
        # Try first to get the posted header filter which is the most recent.
        # Then try to retrieve the header filter from session, then fallback
        hf = header_filters.select_by_id(id,
                                         self.header_filter_id,
                                         default_id,
                                        )

        if hf is None:
            raise NoHeaderFilterAvailable()

        self.header_filter_id = hf.id

        return hf

    def set_entityfilter(self, entity_filters, filter_id, default_id=''):
        """Select an EntityFilter & store it.

        @param entity_filters: EntityFilterList instance
        @param filter_id: ID of the filter to select.
               An empty string means we want to clear the selection.
        @param default_id: ID to use if <filter_id> is not found.
        @return: An EntityFilter instance, or None.
        """
        efilter = None if filter_id == '' else \
                  entity_filters.select_by_id(filter_id,
                                              self.entity_filter_id,
                                              default_id,
                                             )

        self.entity_filter_id = efilter.id if efilter else None

        return efilter

    # def _build_condition(self, pattern, value):
    #     return {pattern.replace('creme-boolean', 'exact'): simple_value(value)}

    # def _date_or_None(self, value, index):
    #     try:
    #         date_str = value[index]
    #     except IndexError:
    #         pass
    #     else:
    #         if str:
    #             try:
    #                 return dt_from_str(date_str).date()
    #             except AttributeError:
    #                 logger.warning('ListViewState: invalid date: %s', str)

    # def _build_date_range_dict(self, name, value):
    #     don = partial(self._date_or_None, value=value)
    #     start = don(index=0)
    #     end = don(index=1)
    #
    #     if not start and not end:
    #         logger.warning('ListViewState: date range need a start and/or a end.')
    #         return {}
    #
    #     return CustomRange(start, end).get_q_dict(name, now())

    # def get_q_with_research(self, model, cells):
    #     query = Q()
    #     rel_searches = []
    #     cf_searches = defaultdict(list)
    #
    #     for item in self.research:
    #         cell_key, value = item
    #         cell = find_first(cells, (lambda cell: cell.key == cell_key), None)
    #
    #         if cell is None:
    #             continue
    #
    #         if isinstance(cell, EntityCellRegularField):
    #             field = cell.field_info[-1]
    #             if isinstance(field, DateField):
    #                 condition = self._build_date_range_dict(cell.value, value)
    #             elif isinstance(field, (ForeignKey, ManyToManyField)) and value[0] == NULL_FK:
    #                 condition = {'{}__isnull'.format(cell.value): True}
    #             else:
    #                 condition = self._build_condition(cell.filter_string, value)
    #
    #             query &= Q(**condition)
    #         elif isinstance(cell, EntityCellRelation):
    #             rel_searches.append((cell.relation_type, value[0]))
    #         elif isinstance(cell, EntityCellFunctionField):
    #             if cell.has_a_filter:
    #                 query &= cell.function_field.filter_in_result(value[0])
    #         elif isinstance(cell, EntityCellCustomField):
    #             cf = cell.custom_field
    #             cf_searches[cf.field_type].append((cf, cell.filter_string, value))
    #
    #     # NB: If we search on several RelationType at the same time, we have to
    #     # build auxiliary queries, because the ORM will join with the Relation
    #     # table only once (& so the result will be empty, because one value
    #     # cannot match several searches).
    #     if rel_searches:
    #         if len(rel_searches) == 1:  # We can optimize these case
    #             rtype, value = rel_searches[0]
    #             query &= Relation.filter_in(model, rtype, value)
    #         else:
    #             for rtype, value in rel_searches:
    #                 query &= Q(pk__in=Relation.objects
    #                                           .filter(type=rtype,
    #                                                   object_entity__header_filter_search_field__icontains=value,
    #                                                  )
    #                                           .values_list('subject_entity', flat=True)
    #                           )
    #
    #     # NB: same remark but with CustomField tables : a type (INT, DATE...) == a DB table.
    #     for field_type, searches in cf_searches.items():
    #         if len(searches) == 1:
    #             cf, pattern, value = searches[0]
    #             related_name = cf.get_value_class().get_related_name()
    #
    #             if field_type == CustomField.DATETIME:
    #                 condition = self._build_date_range_dict('{}__value'.format(related_name), value)
    #             else:
    #                 if field_type in (CustomField.ENUM, CustomField.MULTI_ENUM):
    #                     value = value[0]
    #
    #                     if value == NULL_FK:
    #                         query &= Q(**{'{}__isnull'.format(related_name): True})
    #                         continue
    #
    #                 condition = self._build_condition(pattern, value)
    #
    #             condition.update({'{}__custom_field'.format(related_name): cf})
    #
    #             query &= Q(**condition)
    #         else:
    #             for cf, pattern, value in searches:
    #                 pattern = pattern.partition('__')[2]  # Remove 'tableprefix__'
    #
    #                 if field_type == CustomField.DATETIME:
    #                     condition = self._build_date_range_dict('value', value)
    #                 else:
    #                     if field_type in (CustomField.ENUM, CustomField.MULTI_ENUM):
    #                         value = value[0]
    #
    #                         if value == NULL_FK:
    #                             query &= ~Q(pk__in=cf.get_value_class()
    #                                                  .objects
    #                                                  .filter(custom_field=cf)
    #                                                  .values_list('entity_id', flat=True)
    #                                        )
    #                             continue
    #
    #                     condition = self._build_condition(pattern, value)
    #
    #                 query &= Q(pk__in=cf.get_value_class()
    #                                     .objects
    #                                     .filter(custom_field=cf, **condition)
    #                                     .values_list('entity_id', flat=True)
    #                           )
    #
    #     return query

    # @classmethod
    # def _get_regular_sortfield(cls, cell):
    #     # Compatibility
    #     if cell.filter_string.endswith('__header_filter_search_field__icontains'):
    #         return cell.value + '__header_filter_search_field'
    #
    #     # Related field without subfield
    #     last_field = cell.field_info[-1]
    #
    #     if last_field.is_relation:
    #         # NB: already checked (cell.sortable == True)
    #         # assert not last_field.many_to_many
    #         # assert not last_field.one_to_many
    #         # NB: many_to_one == ForeignKey
    #
    #         subfield_model = last_field.remote_field.model
    #         subfield_ordering = subfield_model._meta.ordering
    #
    #         if not subfield_ordering:
    #             logger.critical('ListViewState: related field model %s should have Meta.ordering set'
    #                             ' (we use "id" as fallback)', subfield_model,
    #                            )
    #
    #             return cell.value + '_id'
    #
    #         return '{}__{}'.format(cell.value, subfield_ordering[0])
    #
    #     return cell.value

    # @classmethod
    # def _get_sortfield(cls, cells_dict, cell_key):
    #     if cell_key is None:
    #         return None
    #
    #     cell = cells_dict.get(cell_key)
    #
    #     if cell is None:
    #         logger.warning('ListViewState: no such sortable column "%s"', cell_key)
    #         return None
    #
    #     if isinstance(cell, EntityCellRegularField):
    #         return cls._get_regular_sortfield(cell)
    #     else:
    #         logger.warning('ListViewState: can not sort with column "%s" '
    #                        '(only sort of regular field is implemented)',
    #                        cell_key,
    #                       )

    # @classmethod
    # def _get_default_sort(cls, model, ordering):
    #     if not ordering:
    #         return None, ''
    #
    #     ofield = cls._OrderedField(ordering[0])
    #
    #     return EntityCellRegularField.build(model, ofield.field_name).key, ofield.order

    # def set_sort(self, model, cells, cell_key, order, fast_mode=False):
    #     """Set the cell-keys which will be used to order the list-view.
    #     @param model: CremeEntity subclass.
    #     @param: cells: Sequence of EntityCells (columns of the list-view)
    #     @param: cell_key: Key of the ordering cell (string).
    #     @param order: string '' or '-'(reverse order).
    #     @param fast_mode: Boolean (True means "There are lots of entities, use a faster/simpler ordering").
    #     @return Tuple of field names, which can be given (with * operator) to QuerySet.order_by().
    #     """
    #     cells_dict = {c.key: c for c in cells if c.sortable}
    #     OField = self._OrderedField
    #
    #     build_cell = partial(EntityCellRegularField.build, model=model)
    #     ordering = [ofield_str
    #                     for ofield_str in model._meta.ordering
    #                         if build_cell(name=OField(ofield_str).field_name).key in cells_dict
    #                ]
    #
    #     # Extra field that is used to internally create the final query ; the
    #     # sort order is toggled by comparing sorting field and column name
    #     # (if it's the same '' <-> '-'), so we can not merge this extra field
    #     # in sort_field, or the toggling will never happen
    #     # (cell.name == sort_field # ==> cell.name != sort_field +'XXX')
    #     sort_field = self._get_sortfield(cells_dict, cell_key)
    #     sort_order = order if order == '-' else ''
    #
    #     if sort_field:
    #         for ordered_field_str in (sort_field, '-' + sort_field):
    #             if ordered_field_str in ordering:
    #                 ordering.remove(ordered_field_str)
    #                 ordering.insert(0, sort_field)
    #
    #                 if sort_order == '-':
    #                     ordering = [str(OField(o).reverse()) for o in ordering]
    #
    #                 break
    #         else:
    #             ordering.insert(0, sort_order + sort_field)
    #     else:
    #         cell_key, sort_order = self._get_default_sort(model, ordering)
    #
    #     self.sort_field = cell_key
    #     self.sort_order = sort_order
    #
    #     # NB: we order by 'id' ('cremeentity_ptr_id') in order to be sure that successive queries
    #     #     give consistent contents. (if you order by 'name' & there are some duplicated names,
    #     #     the order by directive can be respected, but the order of the duplicates in the
    #     #     queries results be different -- so the paginated contents are not consistent).
    #     last_order = sort_order + 'cremeentity_ptr_id'
    #
    #     if ordering:
    #         ind_ordering = get_indexed_ordering(model, ordering + ['*', last_order])
    #         if ind_ordering is not None:
    #             return ind_ordering
    #
    #         if fast_mode:
    #             first_order = ordering[0]
    #             ind_ordering = get_indexed_ordering(model, [first_order, '*', last_order])
    #
    #             return (first_order, last_order) if ind_ordering is None else ind_ordering
    #
    #         return tuple(ordering + [last_order])
    #
    #     return (last_order, )
