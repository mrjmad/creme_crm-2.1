# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2009-2010  Hybird
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

from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required

from assistants.models import ToDo
from assistants.forms.todo import ToDoCreateForm, ToDoEditForm
from assistants.blocks import todos_block
from utils import generic_add, generic_edit, generic_delete


def add(request, entity_id):
    return generic_add(request, entity_id, ToDoCreateForm, u'Nouveau Todo pour <%s>')

def edit(request, todo_id):
    return generic_edit(request, todo_id, ToDo, ToDoEditForm, u"Todo pour <%s>")

@login_required
def validate(request, todo_id):
    todo = get_object_or_404(ToDo, pk=todo_id)
    todo.is_ok = True
    todo.save()
    return HttpResponseRedirect(todo.creme_entity.get_absolute_url())

def delete(request):
    return generic_delete(request, ToDo)

@login_required
def reload_detailview(request, entity_id):
    return todos_block.detailview_ajax(request, entity_id)

@login_required
def reload_home(request):
    return todos_block.home_ajax(request)

@login_required
def reload_portal(request, ct_ids):
    return todos_block.portal_ajax(request, ct_ids)
