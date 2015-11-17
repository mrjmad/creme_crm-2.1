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

import logging
import warnings
import traceback
import sys
from json import dumps as json_dump
from decimal import Decimal

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.http import HttpResponse, Http404
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from ..core.exceptions import ConflictError
from ..signals import pre_replace_related


logger = logging.getLogger(__name__)


def creme_entity_content_types():
    from ..registry import creme_registry
    get_for_model = ContentType.objects.get_for_model
    return (get_for_model(model) for model in creme_registry.iter_entity_models())


def get_ct_or_404(ct_id):
    try:
        ct = ContentType.objects.get_for_id(ct_id)
    except ContentType.DoesNotExist:
        raise Http404('No content type with this id: %s' % ct_id)

    return ct


def build_ct_choices(ctypes):
    from .unicode_collation import collator
    choices = [(ct.id, unicode(ct)) for ct in ctypes]

    sort_key = collator.sort_key
    choices.sort(key=lambda k: sort_key(k[1]))

    return choices


def create_or_update(model, pk=None, **attrs):
    """Get a model instance by its PK, or create a new one ; then set its attributes.
    @param model Django model (class)
    @param pk PK of the wanted instance ; if None, PK is generated by the sql server.
    @param attrs Values of the attributes.
    """
    warnings.warn("create_or_update() function is deprecated ; use QuerySet.update_or_create() instead",
                  DeprecationWarning
                 )

    if pk is not None:
        try:
            instance = model.objects.get(pk=pk)
        except ObjectDoesNotExist:
            instance = model(id=pk)
    else:
        instance = model()

    for key, val in attrs.iteritems():
        setattr(instance, key, val)

    instance.save()

    return instance


def create_if_needed(model, get_dict, **attrs):
    try:
        instance = model.objects.get(**get_dict)
    except model.DoesNotExist:
        attrs.update(get_dict)
        instance = model.objects.create(**attrs)

    return instance


def update_model_instance(obj, **fields):  # TODO: django 1.5: save only modified fields
    """Update the field values of an instance, and save it only if it has changed."""
    save = False

    for f_name, f_value in fields.iteritems():
        if getattr(obj, f_name) != f_value:
            setattr(obj, f_name, f_value)
            save = True

    if save:
        obj.save()

    return save


def replace_related_object(old_instance, new_instance):
    "Replace the references to an instance by references to another one."
    pre_replace_related.send(sender=old_instance.__class__,
                             old_instance=old_instance,
                             new_instance=new_instance,
                            ) # send_robust() ??

#    for rel_objects in old_instance._meta.get_all_related_objects():
    for rel_objects in (f for f in old_instance._meta.get_fields()
                            #if (f.one_to_many or f.one_to_one) and f.auto_created
                            if f.one_to_many
                       ):
        field_name = rel_objects.field.name

        for rel_object in getattr(old_instance, rel_objects.get_accessor_name()).all():
            setattr(rel_object, field_name, new_instance)
            rel_object.save()

#    for rel_objects in old_instance._meta.get_all_related_many_to_many_objects():
    for rel_objects in (f for f in old_instance._meta.get_fields(include_hidden=True)
                            if f.many_to_many and f.auto_created
                       ):
        field_name = rel_objects.field.name

        for rel_object in getattr(old_instance, rel_objects.get_accessor_name()).all():
            m2m_mngr = getattr(rel_object, field_name)
            m2m_mngr.add(new_instance)
            m2m_mngr.remove(old_instance)


# TODO: MUST BE REMOVED WHEN JSON STANDARD LIB HANDLES DECIMAL
class Number2Str(float):
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return str(self.value)


def decimal_serializer(value):
    if isinstance(value, Decimal):
        return Number2Str(value)
    raise TypeError(repr(value) + " is not JSON serializable")


def jsonify(func):
    def _aux(*args, **kwargs):
        status = 200

        try:
            rendered = func(*args, **kwargs)
        except Http404 as e:
            msg = unicode(e)
            status = 404
        except PermissionDenied as e:
            msg = unicode(e)
            status = 403
        except ConflictError as e:
            msg = unicode(e)
            status = 409
        except Exception as e:
            logger.exception('Exception in @jsonify(%s)', func.__name__)
            msg = unicode(e)
            status = 400
        else:
            msg = json_dump(rendered, default=decimal_serializer)

        return HttpResponse(msg, content_type='text/javascript', status=status)

    return _aux


def _get_from_request_or_404(method, method_name, key, cast=None, **kwargs):
    """@param cast A function that cast the return value, and raise an Exception if it is not possible (eg: int)
    """
    value = method.get(key)

    if value is None:
        if 'default' not in kwargs:
            raise Http404('No %s argument with this key: %s' % (method_name, key))

        value = kwargs['default']

    if cast:
        try:
            value = cast(value)
        except Exception as e:
            raise Http404('Problem with argument "%s" : it can not be coerced (%s)' % (key, str(e)))

    return value


def get_from_GET_or_404(GET, key, cast=None, **kwargs):
    return _get_from_request_or_404(GET, 'GET', key, cast, **kwargs)


def get_from_POST_or_404(POST, key, cast=None, **kwargs):
    return _get_from_request_or_404(POST, 'POST', key, cast, **kwargs)


def find_first(iterable, function, *default):
    """
    @param default Optional argument.
    """
    for elt in iterable:
        if function(elt):
            return elt

    if default:
        return default[0]

    raise IndexError


def split_filter(predicate, iterable):
    ok = []
    ko = []

    for x in iterable:
        if predicate(x):
            ok.append(x)
        else:
            ko.append(x)

    return ok, ko


def entities2unicode(entities, user):
    """Return a unicode objects representing a sequence of CremeEntities,
    with care of permissions.
    """
    return u', '.join(entity.allowed_unicode(user) for entity in entities)


def related2unicode(entity, user):
    """Return a unicode object representing a related entity with its owner,
    with care of permissions of this owner.
    """
    return u'%s - %s' % (entity.get_related_entity().allowed_unicode(user), unicode(entity))


__BFS_MAP = {
        'true':  True,
        'false': False,
    }


def bool_from_str(string):
    b = __BFS_MAP.get(string.lower())

    if b is not None:
        return b

    raise ValueError('Can not be coerced to a boolean value: %s' % str(string))


def bool_as_html(b):
    if b:
        checked = 'checked '
        label = _('Yes')
    else:
        checked = ''
        label = _('No')

    return mark_safe(u'<input type="checkbox" %sdisabled/>%s' % (checked, label))


_I2R_NUMERAL_MAP = [(1000, 'M'),  (900, 'CM'), (500, 'D'),  (400, 'CD'), (100, 'C'),
                    (90,   'XC'), (50,  'L'),  (40,  'XL'), (10,  'X'),  (9,   'IX'),
                    (5,    'V'),  (4,   'IV'), (1,   'I'),
                   ]


# Thx to: http://www.daniweb.com/software-development/python/code/216865/roman-numerals-python
def int_2_roman(i):
    "Convert an integer to its roman representation (string)"
    assert i < 4000

    result = []

    for value, numeral in _I2R_NUMERAL_MAP:
        while i >= value:
            result.append(numeral)
            i -= value

    return ''.join(result)


def truncate_str(str, max_length, suffix=""):
    if max_length <= 0:
        return ""

    len_str = len(str)
    if len_str <= max_length and not suffix:
        return str

    total = max_length - len(suffix)
    if total > 0:
        return str[:total] + suffix
    elif total == 0:
        return suffix
    else:
        return str[:total]


def ellipsis(s, length):
    if len(s) > length:
        s = s[:length - 1] + u'…'

    return s


def ellipsis_multi(strings, length):
    str_2_truncate = [[len(s), s] for s in strings]
    total_len = sum(elt[0] for elt in str_2_truncate)

    for i in xrange(max(0, total_len - length)):
        max_idx = -1
        max_value = -1

        for idx, elt in enumerate(str_2_truncate):
            if elt[0] > max_value:
                max_value = elt[0]
                max_idx = idx

        str_2_truncate[max_idx][0] -= 1

    return [ellipsis(elt[1], elt[0]) for elt in str_2_truncate]


def is_testenvironment(request):
    return request.META.get('SERVER_NAME') == 'testserver'


def safe_unicode(value, encodings=None):
    if isinstance(value, unicode):
        return value

    if not isinstance(value, basestring):
        value = value.__unicode__() if hasattr(value, '__unicode__') else repr(value)
        return safe_unicode(value, encodings)

    encodings = encodings or ('utf-8', 'cp1252', 'iso-8859-1',)

    for encoding in encodings:
        try:
            return unicode(value, encoding=encoding)
        except Exception:
            continue

    return unicode(value, encoding='utf-8', errors='replace')


def safe_unicode_error(err, encodings=None):
    #return safe_unicode(err.message)

    # Is this method deprecated for python 3.* (but str/unicode conversions won't be useful at all) ??
    try:
        return unicode(err)
    except:
        pass

    # TODO : keep this deprecated method until migration to python 3.*, because some old APIs may use it in python 2.*
    msg = err.message

    #if isinstance(msg, basestring):
    return safe_unicode(msg, encodings)

    #try:
        #return unicode(msg)
    #except:
        #pass

    #return unicode(err.__class__.__name__)


def log_traceback(logger, limit=10):
    exc_type, exc_value, exc_traceback = sys.exc_info()

    for line in traceback.format_exception(exc_type, exc_value, exc_traceback, limit=limit):
        for split_line in line.split('\n'):
            logger.error(split_line)


def print_traceback(limit=10):
    exc_type, exc_value, exc_traceback = sys.exc_info()
    traceback.print_exception(exc_type, exc_value, exc_traceback, limit=limit)
