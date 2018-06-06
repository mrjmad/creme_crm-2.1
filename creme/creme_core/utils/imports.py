# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2009-2018  Hybird
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

from importlib import import_module
import logging  # warnings

from django.apps import apps


logger = logging.getLogger(__name__)


# def find_n_import(filename, imports):
#     from imp import find_module
#
#     warnings.warn('creme_core.utils.imports.find_n_import() is deprecated ; use import_apps_sub_modules() instead.',
#                   DeprecationWarning
#                  )
#
#     results = []
#
#     for app_config in apps.get_app_configs():
#         app_name = app_config.name
#
#         try:
#             find_module(filename, __import__(app_name, {}, {}, [app_name.split(".")[-1]]).__path__)
#         except (ImportError, TypeError):
#             # There is no app report_backend_register.py, skip it
#             continue
#
#         results.append(__import__("%s.%s" % (app_name, filename), globals(), locals(), imports, -1))
#
#     return results


def import_apps_sub_modules(module_name):
    """Iterate on on installed apps & for each one get a sub-module (if it exists).

    @param module_name: string.
    @return: a list of modules.
    """
    modules = []

    for app_config in apps.get_app_configs():
        try:
            mod = import_module('{}.{}'.format(app_config.name, module_name))
        except ImportError:
            continue
        else:
            modules.append(mod)

    return modules


def import_object(objectpath):
    i = objectpath.rfind('.')
    module, attr = objectpath[:i], objectpath[i+1:]
    try:
        mod = import_module(module)
    except ImportError:
        raise

    try:
        result = getattr(mod, attr)
    except AttributeError:
        raise AttributeError('Module "{}" does not define a "{}" object'.format(module, attr))

    return result


def safe_import_object(objectpath):
    try:
        return import_object(objectpath)
    except Exception as e:
        logger.warn('An error occurred trying to import "%s": [%s]', objectpath, e)
