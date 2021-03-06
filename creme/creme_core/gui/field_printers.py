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

from os.path import splitext

from django.conf import settings
from django.db import models
from django.template.defaultfilters import linebreaks
from django.utils.formats import date_format, number_format
from django.utils.html import escape, format_html, format_html_join
from django.utils.safestring import mark_safe
from django.utils.timezone import localtime
from django.utils.translation import ngettext, gettext as _

from ..models import CremeEntity, EntityFilter, fields
from ..templatetags.creme_widgets import widget_entity_hyperlink, widget_urlize
from ..utils import bool_as_html
from ..utils.collections import ClassKeyedMap
from ..utils.meta import FieldInfo

# TODO: in settings
MAX_HEIGHT = 200
MAX_WIDTH = 200


def image_size(image, max_h=MAX_HEIGHT, max_w=MAX_WIDTH):
    if hasattr(image, 'height'):
        h = image.height
    elif hasattr(image, 'height_field'):
        h = image.height_field
    else:
        h = max_h
    if hasattr(image, 'width'):
        w = image.width
    elif hasattr(image, 'width_field'):
        w = image.width_field
    else:
        w = max_w

    h = float(h)
    w = float(w)

    ratio = max(h / max_h, w / max_w)

    if ratio >= 1.0:
        h /= ratio
        w /= ratio

    return format_html('height="{}" width="{}"', h, w)


def simple_print_html(entity, fval, user, field):
    return escape(fval) if fval is not None else ''


def simple_print_csv(entity, fval, user, field):
    return str(fval) if fval is not None else ''


def print_color_html(entity, fval, user, field):
    return format_html('''<span style="background:#{color};">{color}</span>''', color=fval) if fval else ''


def print_file_html(entity, fval, user, field):
    if fval:
        ext = splitext(fval.path)[1]
        if ext:
            ext = ext[1:]  # remove '.'

        if ext in settings.ALLOWED_IMAGES_EXTENSIONS:
            return print_image_html(entity, fval, user, field)

    return simple_print_html(entity, fval, user, field)


def print_image_html(entity, fval, user, field):
    return format_html(
        """<a onclick="creme.dialogs.image('{url}').open();"><img src="{url}" {size}/></a>""",  # alt="{???}"
        url=fval.url,
        size=image_size(fval),
    ) if fval else ''


def print_integer(entity, fval, user, field):
    if field.choices:  # TODO: manage 'choices' for other types...
        fval = getattr(entity, 'get_{}_display'.format(field.name))()

    # return fval if fval is not None else ''
    return str(fval) if fval is not None else ''


def print_decimal(entity, fval, user, field):
    # TODO remove 'use_l10n' when settings.USE_L10N == True
    return number_format(fval, use_l10n=True) if fval is not None else ''


def print_boolean_html(entity, fval, user, field):
    return bool_as_html(fval) if fval is not None else ''


def print_boolean_csv(entity, fval, user, field):
    if fval is None:
        return ''

    return _('Yes') if fval else _('No')


def print_url_html(entity, fval, user, field):
    return format_html('<a href="{url}" target="_blank">{url}</a>', url=fval) if fval else ''


def print_datetime(entity, fval, user, field):
    return date_format(localtime(fval), 'DATETIME_FORMAT') if fval else ''


def print_date(entity, fval, user, field):
    return date_format(fval, 'DATE_FORMAT') if fval else ''


class FKPrinter:
    @staticmethod
    def print_fk_null_html(entity, user, field):
        null_label = field.get_null_label()
        return format_html('<em>{}</em>', null_label) if null_label else ''

    @staticmethod
    def print_fk_entity_html(entity, fval, user, field):
        return widget_entity_hyperlink(fval, user)

    @staticmethod
    def print_fk_efilter_html(entity, fval, user, field):
        return format_html(
            '<div class="entity_filter-summary">{}<ul>{}</ul></div>',
            fval.name,
            format_html_join(
                '', '<li>{}</li>',
                ((vc,) for vc in fval.get_verbose_conditions(user)),
            )
        )

    def __init__(self, none_printer, default_printer):
        self.none_printer = none_printer
        self._sub_printers = ClassKeyedMap(default=default_printer)

    def __call__(self, entity, fval, user, field):
        return self.none_printer(entity, user, field) if fval is None else \
               self._sub_printers[fval.__class__](entity, fval, user, field)

    def register(self, model, printer):
        self._sub_printers[model] = printer
        return self


print_foreignkey_html = FKPrinter(
    none_printer=FKPrinter.print_fk_null_html,
    default_printer=simple_print_html,
).register(CremeEntity,  FKPrinter.print_fk_entity_html) \
 .register(EntityFilter, FKPrinter.print_fk_efilter_html)


# TODO: FKPrinter() ?
def print_foreignkey_csv(entity, fval, user, field):
    if isinstance(fval, CremeEntity):
        # TODO: change allowed unicode ??
        return str(fval) if user.has_perm_to_view(fval) else settings.HIDDEN_VALUE

    return str(fval) if fval else ''


class M2MPrinter:
    @staticmethod
    def enumerator_all(entity, fval, user, field):
        return fval.all()

    @staticmethod
    def enumerator_entity(entity, fval, user, field):
        return fval.filter(is_deleted=False)

    @staticmethod
    def printer_html(instance, related_entity, fval, user, field):
        return escape(instance)

    @staticmethod
    def printer_entity_html(instance, related_entity, fval, user, field):
        return format_html(
            '<a target="_blank" href="{url}"{attrs}>{content}</a>',
            url=instance.get_absolute_url(),
            attrs=mark_safe(' class="is_deleted"' if instance.is_deleted else ''),
            content=instance.get_entity_summary(user),
        ) if user.has_perm_to_view(instance) else settings.HIDDEN_VALUE

    def __init__(self, default_printer, default_enumerator):
        self._sub_printers = ClassKeyedMap(default=(default_printer, default_enumerator))

    def __call__(self, entity, fval, user, field):
        printer, enumerator = self._sub_printers[fval.model]
        li_tags = format_html_join(
            '', '<li>{}</li>',
            ((printer(e, entity, fval, user, field),) for e in enumerator(entity, fval, user, field))
        )

        return format_html('<ul>{}</ul>', li_tags) if li_tags else ''

    def register(self, model, printer, enumerator):
        self._sub_printers[model] = (printer, enumerator)
        return self

print_many2many_html = M2MPrinter(default_printer=M2MPrinter.printer_html,
                                  default_enumerator=M2MPrinter.enumerator_all,
                                 ).register(CremeEntity,
                                            printer=M2MPrinter.printer_entity_html,
                                            enumerator=M2MPrinter.enumerator_entity,
                                           )


# TODO: M2MPrinter ??
def print_many2many_csv(entity, fval, user, field):
    if issubclass(fval.model, CremeEntity):
        # TODO: CSV summary ?? [e.get_entity_m2m_summary(user)]
        return '/'.join(
            str(e) if user.has_perm_to_view(e) else settings.HIDDEN_VALUE
                for e in fval.filter(is_deleted=False)
        )

    return '/'.join(str(a) for a in fval.all())


def print_duration(entity, fval, user, field):
    try:
        h, m, s = fval.split(':')
    except (ValueError, AttributeError):
        return ''

    h = int(h)
    m = int(m)
    s = int(s)

    return '{hour} {hour_label} {minute} {minute_label} {second} {second_label}'.format(
        hour=h,
        hour_label=ngettext('hour', 'hours', h),
        minute=m,
        minute_label=ngettext('minute', 'minutes', m),
        second=s,
        second_label=ngettext('second', 'seconds', s)
    )


def print_email_html(entity, fval, user, field):
    return format_html('<a href="mailto:{email}">{email}</a>', email=fval) if fval else ''


def print_text_html(entity, fval, user, field):
    # return linebreaks(widget_urlize(fval, autoescape=True)) if fval else ''
    return mark_safe(linebreaks(widget_urlize(fval, autoescape=True))) if fval else ''


def print_unsafehtml_html(entity, fval, user, field):
    return linebreaks(fval, autoescape=True) if fval else ''


# TODO: Do more specific fields (i.e: currency field....) ?
class _FieldPrintersRegistry:
    def __init__(self):
        self._printers = ClassKeyedMap([
                (models.IntegerField,       print_integer),

                (models.FloatField,         print_decimal),
                (models.DecimalField,       print_decimal),

                (models.BooleanField,       print_boolean_html),
                (models.NullBooleanField,   print_boolean_html),

                (models.DateField,          print_date),
                (models.DateTimeField,      print_datetime),

                (models.TextField,          print_text_html),
                (models.EmailField,         print_email_html),
                (models.URLField,           print_url_html),

                (models.FileField,          print_file_html),
                (models.ImageField,         print_image_html),

                (models.ForeignKey,         print_foreignkey_html),
                (models.ManyToManyField,    print_many2many_html),
                (models.OneToOneField,      print_foreignkey_html),

                (fields.DurationField,      print_duration),
                (fields.DatePeriodField,    simple_print_html),  # TODO: JSONField ?

                (fields.ColorField,         print_color_html),

                (fields.UnsafeHTMLField,    print_unsafehtml_html),
            ],
            default=simple_print_html,
        )
        self._csv_printers = ClassKeyedMap([
                (models.IntegerField,       print_integer),

                (models.FloatField,         print_decimal),
                (models.DecimalField,       print_decimal),

                (models.BooleanField,       print_boolean_csv),
                (models.NullBooleanField,   print_boolean_csv),

                (models.DateField,          print_date),
                (models.DateTimeField,      print_datetime),
                # (models.ImageField,         print_image_csv, TODO ??

                (models.ForeignKey,         print_foreignkey_csv),
                (models.ManyToManyField,    print_many2many_csv),
                (models.OneToOneField,      print_foreignkey_csv),

                (fields.DurationField,      print_duration),
            ],
            default=simple_print_csv,
        )

        self._printers_maps = {
            'html': self._printers,
            'csv':  self._csv_printers,
        }

        css_default        = getattr(settings, 'CSS_DEFAULT_LISTVIEW')
        css_default_header = getattr(settings, 'CSS_DEFAULT_HEADER_LISTVIEW')

        css_number_listview      = getattr(settings, 'CSS_NUMBER_LISTVIEW',      css_default)
        css_textarea_listview    = getattr(settings, 'CSS_TEXTAREA_LISTVIEW',    css_default)
        css_date_header_listview = getattr(settings, 'CSS_DATE_HEADER_LISTVIEW', css_default_header)

        self._listview_css_printers = ClassKeyedMap([
                (models.IntegerField,               css_number_listview),
                (models.CommaSeparatedIntegerField, css_number_listview),
                (models.DecimalField,               css_number_listview),
                (models.FloatField,                 css_number_listview),

                (models.TextField,                  css_textarea_listview),
            ],
            default=css_default,
        )

        self._header_listview_css_printers = ClassKeyedMap([
                (models.DateField,      css_date_header_listview),
                (models.DateTimeField,  css_date_header_listview),
            ],
            default=css_default_header,
        )

    def register(self, field, printer, output='html'):
        """Register a field printer.
        @param field: A class inheriting django.models.Field.
        @param printer: A callable object. See simple_print_html() for arguments/return.
        @param output: string in {'html', 'csv'}.
        """
        self._printers_maps[output][field] = printer

    def register_listview_css_class(self, field, css_class, header_css_class):
        """Register a listview css class for field.
        @param field: A class inheriting django.models.Field
        @param css_class: A string.
        """
        self._listview_css_printers[field] = css_class
        self._header_listview_css_printers[field] = header_css_class

    def get_listview_css_class_for_field(self, field_class):
        return self._listview_css_printers[field_class]

    def get_header_listview_css_class_for_field(self, field_class):
        return self._header_listview_css_printers[field_class]

    def _build_field_printer(self, field_info, output='html'):
        base_field = field_info[0]
        base_name = base_field.name
        HIDDEN_VALUE = settings.HIDDEN_VALUE

        if len(field_info) > 1:
            # base_model = base_field.rel.to
            base_model = base_field.remote_field.model
            sub_printer = self._build_field_printer(field_info[1:], output)

            if isinstance(base_field, models.ForeignKey):
                if issubclass(base_model, CremeEntity):
                    def printer(obj, user):
                        base_value = getattr(obj, base_name)

                        if base_value is None:
                            return ''

                        if not user.has_perm_to_view(base_value):
                            return HIDDEN_VALUE

                        return sub_printer(base_value, user)
                else:
                    def printer(obj, user):
                        base_value = getattr(obj, base_name)

                        if base_value is None:
                            return ''

                        return sub_printer(base_value, user)
            else:
                assert isinstance(base_field, models.ManyToManyField)

                if issubclass(base_model, CremeEntity):
                    def sub_values(obj, user):
                        has_perm = user.has_perm_to_view

                        for e in getattr(obj, base_name).filter(is_deleted=False):
                            if not has_perm(e):
                                yield HIDDEN_VALUE
                            else:
                                sub_value = sub_printer(e, user)
                                if sub_value:  # NB: avoid empty string
                                    yield sub_value

                    if output == 'csv':
                        def printer(obj, user):
                            return '/'.join(sub_values(obj, user))
                    else:
                        def printer(obj, user):
                            li_tags = format_html_join(
                                '', '<li>{}</li>', ((v,) for v in sub_values(obj, user))
                            )

                            return format_html('<ul>{}</ul>', li_tags) if li_tags else ''
                else:
                    def sub_values(obj, user):
                        for a in getattr(obj, base_name).all():
                            sub_value = sub_printer(a, user)
                            if sub_value:  # NB: avoid empty string
                                yield sub_value

                    if output == 'csv':
                        def printer(obj, user):
                            return '/'.join(sub_values(obj, user))
                    else:
                        def printer(obj, user):
                            li_tags = format_html_join(
                                '', '<li>{}</li>', ((v,) for v in sub_values(obj, user))
                            )

                            return format_html('<ul>{}</ul>', li_tags) if li_tags else ''
        else:
            print_func = self._printers_maps[output][base_field.__class__]

            def printer(obj, user):
                return print_func(obj, getattr(obj, base_name), user, base_field)

        return printer

    def build_field_printer(self, model, field_name, output='html'):
        return self._build_field_printer(FieldInfo(model, field_name), output=output)

    def get_html_field_value(self, obj, field_name, user):
        return self.build_field_printer(obj.__class__, field_name)(obj, user)

    def get_csv_field_value(self, obj, field_name, user):
        return self.build_field_printer(obj.__class__, field_name, output='csv')(obj, user)


field_printers_registry = _FieldPrintersRegistry()
