# -*- coding: utf-8 -*-

import logging
import re

logger = logging.getLogger(__name__)


SMALL = 'a|an|and|as|at|but|by|en|for|if|in|of|on|or|the|to|v\.?|via|vs\.?'
PUNCT = r"""!"#$%&'‘()*+,\-./:;?@\\\[\]_`{|}~"""
SMALL_WORDS = re.compile(r'^(%s)$' % SMALL, re.I)
INLINE_PERIOD = re.compile(r'[a-z][.][a-z]', re.I)
UC_ELSEWHERE = re.compile(r'[%s]*?[a-zA-Z]+[A-Z]+?' % PUNCT)
CAPFIRST = re.compile(r"^[%s]*?([A-Za-z])" % PUNCT)
SMALL_FIRST = re.compile(r'^([%s]*)(%s)\b' % (PUNCT, SMALL), re.I)
SMALL_LAST = re.compile(r'\b(%s)[%s]?$' % (SMALL, PUNCT), re.I)
SUBPHRASE = re.compile(r'([:.;?!][ ])(%s)' % SMALL)
APOS_SECOND = re.compile(r"^[dol]{1}['‘]{1}[a-z]+$", re.I)
ALL_CAPS = re.compile(r'^[0-9A-Z\s%s]+$' % PUNCT)
UC_INITIALS = re.compile(r"^(?:[A-Z]{1}\.{1}|[A-Z]{1}\.{1}[A-Z]{1})+$")
MAC_MC = re.compile(r"^(?![Mm]ach.*|[Mm]acro.*)([Mm]a?c)(\w+)")


def title_case(text):
    """
    title_case is a filter function that changes all words in text to Title Caps,
    and attempts to be clever about *un*capitalizing SMALL words like a/an/the in the input.

    The list of "SMALL words" which are not capped comes from
    the New York Times Manual of Style, plus 'vs' and 'v'.

    Original Perl version by: John Gruber http://daringfireball.net/ 10 May 2008
    Python version by Stuart Colville http://muffinresearch.co.uk
    License: http://www.opensource.org/licenses/mit-license.php

    :param text: string of text to be title cased
    :return: title cased string
    """

    lines = re.split('[\r\n]+', text)
    processed = []
    for line in lines:
        all_caps = ALL_CAPS.match(line)
        words = re.split('[\t ]', line)
        tc_line = []
        for word in words:
            if all_caps:
                if UC_INITIALS.match(word):
                    tc_line.append(word)
                    continue
                else:
                    word = word.lower()

            if APOS_SECOND.match(word):
                word = word.replace(word[0], word[0].upper())
                word = word.replace(word[2], word[2].upper())
                tc_line.append(word)
                continue
            if INLINE_PERIOD.search(word) or UC_ELSEWHERE.match(word):
                tc_line.append(word)
                continue
            if SMALL_WORDS.match(word):
                tc_line.append(word.lower())
                continue

            match = MAC_MC.match(word)
            if match:
                tc_line.append("%s%s" % (match.group(1).capitalize(),
                                         match.group(2).capitalize()))
                continue

            if "/" in word and not "//" in word:
                slashed = []
                for item in word.split('/'):
                    slashed.append(CAPFIRST.sub(lambda m: m.group(0).upper(), item))
                tc_line.append("/".join(slashed))
                continue

            hyphenated = []
            for item in word.split('-'):
                hyphenated.append(CAPFIRST.sub(lambda m: m.group(0).upper(), item))
            tc_line.append("-".join(hyphenated))

        result = " ".join(tc_line)

        result = SMALL_FIRST.sub(lambda m: '%s%s' % (
            m.group(1),
            m.group(2).capitalize()
        ), result)

        result = SMALL_LAST.sub(lambda m: m.group(0).capitalize(), result)

        result = SUBPHRASE.sub(lambda m: '%s%s' % (
            m.group(1),
            m.group(2).capitalize()
        ), result)

        processed.append(result)

    return '\n'.join(processed)


class DimensionCache(object):
    """DimensionCache is a helper object to reduce code footprint of initializing and merging dimension records.

    Args:
        connection (sqlalchemy.engine.base.OrmConnection): sqlalchemy database connection
        model (sqlalchemy.ext.declarative.api.DeclarativeMeta): sqlalchemy data model
        key_columns (iterable): key columns to use for caching (iterable should be ordered for consistency)
        cache_object (Optional[boolean]): indicates if cache should be initialized (default is True)
        where_clause (Optional[sqlalchemy.sql.elements.BinaryExpression]): sqlalchemy expression for filter
    """

    def __init__(self, connection, model, key_columns, init_cache=True, where_clause=None):
        self._cache = {}
        self._connection = connection
        self._key_columns = tuple(key_columns)
        self._model = model
        self.counts = {'exist': 0, 'insert': 0}     # keeps track of cache hits and new inserts

        if init_cache:
            logger.info('Caching {0}'.format(model.__tablename__))
            projection = [self._model.id] + [getattr(self._model, kc) for kc in self._key_columns]
            dimension_query = self._connection.session.query(*projection)
            if where_clause is not None:
                dimension_query = dimension_query.filter(where_clause)
            for d in dimension_query:
                self._cache[tuple(v for v in d[1:])] = d[0]

    def lookup(self, key):
        """Accessor method for performing a cache lookup

        Args:
            key (tuple): cache key

        Returns:
            int: dimension id for the given key in the cache
        """
        return self._cache.get(key)

    def merge(self, record):
        """Merge a record to the database.

        Args:
            record: dictionary containing column-value as the key-column pairs

        Returns:
            int: dimension id for the record generated/returned

        Note:
            Connection is only flushed.  Persistence of record will have to be performed outside class scope.
        """
        key = tuple([record[kc] for kc in self._key_columns])
        cache_id = self.lookup(key)
        if cache_id is None:
            d = self._model.from_dict(record, subset=[c.name for c in self._model.__table__.columns])
            self._connection.session.add(d)
            self._connection.session.flush()
            cache_id = self._cache[key] = d.id
            self.counts['insert'] += 1
        else:
            self.counts['exist'] += 1

        return cache_id
