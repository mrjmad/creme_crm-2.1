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

# from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404  # redirect

# from creme.creme_core.auth import build_creation_perm as cperm
from creme.creme_core.auth.decorators import login_required  # permission_required
# from creme.creme_core.models import CremeEntity
from creme.creme_core.utils import get_from_POST_or_404
from creme.creme_core.views import generic
from creme.creme_core.views.decorators import jsonify

from creme import products

from ..constants import DEFAULT_HFILTER_PRODUCT
from ..forms import product as product_forms
from ..models import Category, SubCategory

from .base import ImagesAddingBase

Product = products.get_product_model()
Service = products.get_service_model()

# Function views --------------------------------------------------------------


# def abstract_add_product(request, form=product_forms.ProductCreateForm,
#                          submit_label=Product.save_label,
#                         ):
#     warnings.warn('products.views.product.abstract_add_product() is deprecated ; '
#                   'use the class-based view ProductCreation instead.',
#                   DeprecationWarning
#                  )
#     return generic.add_entity(request, form,
#                               extra_template_dict={'submit_label': submit_label},
#                              )


# def abstract_edit_product(request, product_id, form=product_forms.ProductEditForm):
#     warnings.warn('products.views.product.abstract_edit_product() is deprecated ; '
#                   'use the class-based view ProductEdition instead.',
#                   DeprecationWarning
#                  )
#     return generic.edit_entity(request, product_id, Product, form)


# def abstract_view_product(request, product_id,
#                           template='products/view_product.html',
#                          ):
#     warnings.warn('products.views.product.abstract_view_product() is deprecated ; '
#                   'use the class-based view ProductDetail instead.',
#                   DeprecationWarning
#                  )
#     return generic.view_entity(request, product_id, Product, template=template)


# @login_required
# @permission_required(('products', cperm(Product)))
# def add(request):
#     warnings.warn('products.views.product.add() is deprecated.', DeprecationWarning)
#     return abstract_add_product(request)


# @login_required
# @permission_required('products')
# def edit(request, product_id):
#     warnings.warn('products.views.product.edit() is deprecated.', DeprecationWarning)
#     return abstract_edit_product(request, product_id)


# @login_required
# @permission_required('products')
# def detailview(request, product_id):
#     warnings.warn('products.views.product.detailview() is deprecated.', DeprecationWarning)
#     return abstract_view_product(request, product_id)


# @login_required
# @permission_required('products')
# def listview(request):
#     return generic.list_view(request, Product, hf_pk=DEFAULT_HFILTER_PRODUCT)


@jsonify
@login_required
def get_subcategories(request, category_id):
    get_object_or_404(Category, pk=category_id)
    return [*SubCategory.objects.filter(category=category_id)
                                .order_by('id')
                                .values_list('id', 'name')
           ]


# @login_required
# @permission_required('products')
# def remove_image(request, entity_id):
#     img_id = get_from_POST_or_404(request.POST, 'id')
#     entity = get_object_or_404(CremeEntity, pk=entity_id).get_real_entity()
#
#     if not isinstance(entity, (Product, Service)):
#         raise Http404('Entity should be a Product/Service')
#
#     request.user.has_perm_to_change_or_die(entity)
#
#     entity.images.remove(img_id)
#
#     if request.is_ajax():
#         return HttpResponse()
#
#     return redirect(entity)
class ImageRemoving(generic.base.EntityRelatedMixin, generic.CremeDeletion):
    permissions = 'products'
    entity_classes = [Product, Service]

    image_id_arg = 'id'

    def perform_deletion(self, request):
        img_id = get_from_POST_or_404(request.POST, self.image_id_arg, cast=int)
        self.get_related_entity().images.remove(img_id)


# Class-based views  ----------------------------------------------------------

class ProductCreation(generic.EntityCreation):
    model = Product
    form_class = product_forms.ProductCreateForm


class ProductDetail(generic.EntityDetail):
    model = Product
    template_name = 'products/view_product.html'
    pk_url_kwarg = 'product_id'


class ProductEdition(generic.EntityEdition):
    model = Product
    form_class = product_forms.ProductEditForm
    pk_url_kwarg = 'product_id'


class ProductsList(generic.EntitiesList):
    model = Product
    default_headerfilter_id = DEFAULT_HFILTER_PRODUCT


class ImagesAdding(ImagesAddingBase):
    entity_id_url_kwarg = 'product_id'
    entity_classes = Product
