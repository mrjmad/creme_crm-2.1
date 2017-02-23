# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2015-2017  Hybird
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

from django.utils.translation import ugettext_lazy as _

from creme.creme_core.apps import CremeAppConfig


class CrudityConfig(CremeAppConfig):
    name = 'creme.crudity'
    verbose_name = _(u'External data management')
    dependencies = ['creme.creme_core']

    def ready(self):
        super(CrudityConfig, self).ready()

        from . import signals

    # def register_creme_app(self, creme_registry):
    #     creme_registry.register_app('crudity', _(u'External data management'), '/crudity')

    def register_menu(self, creme_menu):
        from django.conf import settings
        from django.core.urlresolvers import reverse_lazy as reverse

        if settings.OLD_MENU:
            reg_item = creme_menu.register_app('crudity', '/crudity/').register_item
            # reg_item('/crudity/waiting_actions', _(u'Email waiting actions'), 'crudity')
            # reg_item('/crudity/history',         _(u'History'),               'crudity')
            reg_item(reverse('crudity__actions'), _(u'Email waiting actions'), 'crudity')
            reg_item(reverse('crudity__history'), _(u'History'),               'crudity')
        else:
            URLItem = creme_menu.URLItem
            creme_menu.get('features', 'tools') \
                      .add(URLItem('crudity-waiting_actions', url=reverse('crudity__actions'),
                                   label=_(u'Email waiting actions'), perm='crudity',
                                  ),
                           priority=250,
                          ) \
                      .add(URLItem('crudity-history', reverse('crudity__history'),
                                   label=_(u'History of automatised creation'), perm='crudity',
                                  ),
                           priority=260,
                          )

    def register_setting_key(self, setting_key_registry):
        from .setting_keys import sandbox_key

        setting_key_registry.register(sandbox_key)
