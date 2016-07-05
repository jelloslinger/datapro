# -*- coding: utf-8 -*-

import logging

from sqlalchemy import create_engine
from sqlalchemy.engine.url import make_url, URL
from sqlalchemy.orm import sessionmaker

from datapro.base.util import dict_merge

logger = logging.getLogger(__name__)


class Connection(object):

    _CONFIG = {
        'db': {
            # 'admin': {
            #     'drivername': 'mysql',
            #     'host': '127.0.0.1',
            #     'password': 'abc123',
            #     'username': 'root'
            # }
        }
    }

    def __init__(self, name, config=None):

        # exit(config)

        if config is None:
            logger.warn('No configuration was passed.')
            config = {}

        config.setdefault('db', {})

        try:
            self._config = dict_merge(Connection._CONFIG, config)['db'][name]
        except KeyError:
            raise ConnectionException('Connection name, {0}, not defined in configuration'.format(name))

        # First, try creating the url by passing the configuration to the URL object.
        try:
            self._config['database'] = name
            self.url = URL(**self._config)
        except TypeError:
            # Second, try making the URL by passing a connection string into the make_url function.
            # NOTE: this is handy for when you are connecting through a DSN
            try:
                self.url = make_url(self._config['connection_string'])
            except KeyError:
                raise ConnectionException('Could not resolve configuration.')

        self.engine = create_engine(self.url, convert_unicode=True, pool_recycle=14400)  # 4-hour recycle


class OrmConnection(Connection):

    def __init__(self, name, config=None, autocommit=False, flush_block_size=10000, expire_on_commit=False):
        super(OrmConnection, self).__init__(name, config=config)
        self._flush_count = 0
        self.flush_block_size = flush_block_size
        self.session = sessionmaker(bind=self.engine, autocommit=autocommit, expire_on_commit=expire_on_commit)()

    def block_flush(self):
        self._flush_count += 1
        if self._flush_count >= self.flush_block_size:
            self._flush_count = 0
            self.session.flush()
            return True
        return False


class ConnectionException(Exception):
    pass
