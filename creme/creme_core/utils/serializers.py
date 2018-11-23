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

from datetime import datetime, time, timezone, timedelta
from decimal import Decimal
from json import dumps as json_dumps
from types import GeneratorType

from django.core.serializers.json import DjangoJSONEncoder
from django.utils.timezone import is_aware, make_aware

from creme.creme_core.utils.dates import dt_to_ISO8601, to_utc


# TODO: MUST BE REMOVED WHEN JSON STANDARD LIB HANDLES DECIMAL
class Number2Str(float):
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return str(self.value)


class CremeJSONEncoder(DjangoJSONEncoder):
    use_utc = True

    def __init__(self, use_utc=True, **kwargs):
        """
            @param use_utc: (default=True) forces all time/datetime objects to UTC representation.
                        e.g: The datetime '12-01-2018 at 08:12:25.012345 (US/Eastern, -0500)' will become
                             - "2018-01-12T13:12:25.012Z" (use_utc=True)
                             - "2018-01-12T08:12:25.012-05:00" (use_utc=False)
        """
        self.use_utc = use_utc
        super().__init__(**kwargs)

    def _encode_time(self, value):
        if self.use_utc:
            dt_value = datetime.combine(datetime.today(), value)

            if is_aware(dt_value):
                dt_value = make_aware(to_utc(dt_value), timezone.utc)

            r = dt_value.isoformat(timespec='milliseconds')[11:]
        else:
            # HACK : utcoffset is None for an AWARE datetime.time
            if value.tzinfo is not None:
                r = datetime.combine(datetime.today(), value).isoformat(timespec='milliseconds')[11:]
            else:
                r = value.isoformat(timespec='milliseconds')

        if r.endswith('+00:00'):
            r = r[:-6] + 'Z'

        return r

    def _encode_datetime(self, value):
        if self.use_utc:
            if is_aware(value):
                value = make_aware(to_utc(value), timezone.utc)

            r = value.isoformat(timespec='milliseconds')

            if r.endswith('+00:00'):
                r = r[:-6] + 'Z'

            return r
        else:
            return super().default(value)

    def default(self, o):
        if isinstance(o, Decimal):
            return Number2Str(o)
        elif isinstance(o, time):
            return self._encode_time(o)
        elif isinstance(o, datetime):
            return self._encode_datetime(o)

        return super().default(o)


def json_encode(value, separators=(',', ':'), cls=CremeJSONEncoder, use_utc=True, **kwargs):
    """
        Encode data to json with improved handling of datetime objects.
        @param value: object or generator
        @param separators: json format separators (see json.dumps)
        @param cls: json encoder class
        
    """
    return json_dumps(list(value) if isinstance(value, GeneratorType) else value,
                      separators=separators,
                      cls=cls,
                      use_utc=use_utc,
                      **kwargs
                     )
