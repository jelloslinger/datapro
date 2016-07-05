# -*- coding: utf-8 -*-

import datetime
import logging
import time
from decimal import Decimal, ROUND_HALF_UP

import xlrd

from datapro.base.util import to_utc

logger = logging.getLogger(__name__)


class Validator(object):

    def __init__(self):
        self._message_template = None
        self.properties = None
        self.valid = None

        self.reset()

    def _check_null(self, key, value, blank_is_null, nulls_ok, message_template):
        if value is None:
            if nulls_ok:
                self.properties[key] = value
            else:
                self._fail(key, 'Nulls are not allowed', message_template)
            return False
        elif isinstance(value, str) and value == '':
            if blank_is_null:
                if nulls_ok:
                    self.properties[key] = None
                else:
                    self._fail(key, 'Blank strings are not allowed', message_template)
                return False
        return True

    def _fail(self, key, message, message_template):
        self.valid = False
        if not message_template:
            message_template = self._message_template

        logger.warn(message_template.format(key=key, message=message))

    def reset(self, mesage_template=None):
        if mesage_template:
            self._message_template = mesage_template
        self.properties = {}
        self.valid = True

    def date(self, key, value, format, nulls_ok=False, message_template=None):
        if self._check_null(key, value, True, nulls_ok, message_template):
            if isinstance(format, str):
                try:
                    self.properties[key] = datetime.date(*(time.strptime(value, format)[:3]))
                except:
                    self._fail(key, '"{0}" could not be converted to a date'.format(value), message_template)
            else:
                try:
                    self.properties[key] = datetime.date(*(xlrd.xldate_as_tuple(value, format)[:3]))
                except:
                    self._fail(key, '"{0}" could not be converted to a date'.format(value), message_template)

    def datetime(self, key, value, format, tz=None, nulls_ok=False, message_template=None):
        if self._check_null(key, value, True, nulls_ok, message_template):
            if isinstance(format, str):
                try:
                    dt = datetime.datetime(*(time.strptime(value, format)[:6]))
                except:
                    self._fail(key, '"{0}" could not be converted to a date and time'.format(value), message_template)
                    return
            else:
                try:
                    dt = datetime.datetime(*(xlrd.xldate_as_tuple(value, format)[:6]))
                except:
                    self._fail(key, '"{0}" could not be converted to a date and time'.format(value), message_template)
                    return

            if tz is not None:
                dt = to_utc(dt, tz)
            self.properties[key] = dt

    def decimal(self, key, value, precision, nulls_ok=False, message_template=None):
        if self._check_null(key, value, True, nulls_ok, message_template):
            qp = '1.{places}'.format(places='0'*precision)
            try:
                self.properties[key] = Decimal(value).quantize(Decimal(qp), rounding=ROUND_HALF_UP)
            except:
                self._fail(key, '"{0}" could not be converted to a number'.format(value), message_template)

    def int(self, key, value, nulls_ok=False, message_template=None):
        if self._check_null(key, value, True, nulls_ok, message_template):
            try:
                self.properties[key] = int(value)
            except:
                self._fail(key, '"{0}" could not be converted to an integer'.format(value), message_template)

    def lookup(self, key, value, dictionary, miss_ok=False, nulls_ok=False, message_template=None):
        if self._check_null(key, value, False, nulls_ok, message_template):
            if isinstance(value, str):
                if value == '':
                    self._fail(key, 'Blank strings are not allowed', message_template)

            if value in dictionary:
                self.properties[key] = dictionary[value]
            elif miss_ok:
                self.properties[key] = None
            else:
                self._fail(key, '"{0}" is not in mapping'.format(value), message_template)

    def string(self, key, value, blanks_ok=False, convert_nulls_to_blank=False, max_length=0, nulls_ok=False, message_template=None):

        if value is None:
            if convert_nulls_to_blank:
                if blanks_ok:
                    self.properties[key] = ''
                else:
                    self._fail(key, 'Interpreted null as blank, but blank strings are not allowed', message_template)
            elif not nulls_ok:
                self._fail(key, 'Nulls are not allowed', message_template)
        elif value == '' and not blanks_ok:
            self._fail(key, 'Blank strings are not allowed', message_template)
        else:
            if 0 < max_length < len(str(value)):
                self._fail(
                    key,
                    '"{0}" is {1} characters long, but the maximum allowed length is {2}'.format(
                        value,
                        len(str(value)),
                        max_length
                    ),
                    message_template
                )
            else:
                self.properties[key] = str(value)
