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

from django.contrib.auth.decorators import login_required, permission_required

from creme_core.views.generic import add_entity, edit_entity, view_entity, list_view

from documents.models.document import Document
from documents.forms.document import DocumentCreateForm, DocumentCreateViewForm, DocumentEditForm


@login_required
@permission_required('documents')
@permission_required('documents.add_document')
def add(request):
    return add_entity(request, DocumentCreateForm)

@login_required
@permission_required('documents')
@permission_required('documents.add_document')
def add_from_detailview(request):
    req_get = request.REQUEST.get

    #TODO: credentials on linked entity ??

    return add_entity(request, DocumentCreateViewForm, req_get('callback_url'),
                      extra_initial={'entity_id': req_get('entity_id')})

@login_required
@permission_required('documents')
def edit(request, document_id):
    return edit_entity(request, document_id, Document, DocumentEditForm)

@login_required
@permission_required('documents')
def detailview(request, object_id):
    return view_entity(request, object_id, Document, '/documents/document', 'documents/view_document.html')

@login_required
@permission_required('documents')
def listview(request):
    return list_view(request, Document, extra_dict={'add_url': '/documents/document/add'})
