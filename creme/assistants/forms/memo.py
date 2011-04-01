# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2009-2011  Hybird
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

from datetime import datetime

from creme_core.forms import CremeModelWithUserForm

from assistants.models import Memo


class MemoEditForm(CremeModelWithUserForm):
    class Meta:
        model = Memo
        exclude = ('creation_date', 'entity_content_type', 'entity_id')

    def __init__(self, entity, *args, **kwargs):
        super(MemoEditForm, self).__init__(*args, **kwargs)
        self.entity = entity

    def save (self, *args, **kwargs):
        instance = self.instance
        instance.creme_entity = self.entity
        instance.user = self.cleaned_data['user']

        return super(MemoEditForm, self).save(*args, **kwargs)


class MemoCreateForm(MemoEditForm):
    def save(self, *args, **kwargs):
        self.instance.creation_date = datetime.now()

        return super(MemoCreateForm, self).save(*args, **kwargs)
