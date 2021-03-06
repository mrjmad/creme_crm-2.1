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

# import warnings

from django.forms import ModelMultipleChoiceField, CharField
from django.utils.translation import gettext_lazy as _, gettext

from ..models import CremePropertyType, CremeProperty
from ..utils import entities2unicode

from .base import CremeForm
from .widgets import Label


class _AddPropertiesForm(CremeForm):
    types = ModelMultipleChoiceField(label=_('Type of property'),
                                     queryset=CremePropertyType.objects.none(),
                                    )

    # def _create_properties(self, entities, ptypes):
    #     warnings.warn('creme_core.forms.creme_property._AddPropertiesForm._create_properties() is deprecated ;'
    #                   'use CremeProperty.objects.safe_multi_save() instead.',
    #                   DeprecationWarning
    #                  )
    #
    #     property_get_or_create = CremeProperty.objects.get_or_create
    #
    #     for entity in entities:
    #         for ptype in ptypes:
    #             property_get_or_create(type=ptype, creme_entity=entity)


class AddPropertiesForm(_AddPropertiesForm):
    def __init__(self, entity, *args, **kwargs):
        # We need this entity in super constructor when post_init_callback is called.
        # TODO: Add unit tests for this !
        self.entity = entity
        super().__init__(*args, **kwargs)

        excluded = CremeProperty.objects.filter(creme_entity=entity.id) \
                                        .values_list('type', flat=True)
        self.fields['types'].queryset = CremePropertyType.objects\
                                                         .compatible(type(entity))\
                                                         .exclude(pk__in=excluded)

    def save(self):
        create = CremeProperty.objects.safe_create

        for ptype in self.cleaned_data['types']:
            create(creme_entity=self.entity, type=ptype)


class AddPropertiesBulkForm(_AddPropertiesForm):
    entities_lbl = CharField(label=_('Related entities'), widget=Label(), required=False)

    def __init__(self, model, entities, forbidden_entities, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.entities = entities
        fields = self.fields

        fields['types'].queryset = CremePropertyType.objects.compatible(model)  # TODO: Sort?
        fields['entities_lbl'].initial = entities2unicode(entities, self.user) \
                                         if entities else \
                                         gettext('NONE !')

        if forbidden_entities:
            fields['bad_entities_lbl'] = CharField(
                label=gettext('Uneditable entities'),
                widget=Label, required=False,
                initial=entities2unicode(forbidden_entities, self.user),
            )

    def save(self):
        CremeProperty.objects.safe_multi_save(
            [CremeProperty(type=ptype, creme_entity=entity)
                for entity in self.entities
                    for ptype in self.cleaned_data['types']
            ]
        )
