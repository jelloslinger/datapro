# -*- coding: utf-8 -*-
"""Base Classes for ETL jobs.

These classes represent the base building blocks to create ETL jobs.

Example:
    TODO
"""

import datetime
import logging

from datapro.base.util import dict_merge
from datapro.base.interface import IFramework

# ETL Job Statuses
STATUS_FAIL = 'failed'
STATUS_RUN = 'running'
STATUS_PAUSE = 'paused'
STATUS_START = 'started'
STATUS_STOP = 'stopped'

logger = logging.getLogger(__name__)


class BaseConfig(dict):
    """Base Configuration

    Adds merge functionality to a Python dictionary.

    Args:
        initial_dict (Optional[dict]): injection of the Python dictionary
    """

    def __init__(self, initial_dict={}):
        super(BaseConfig, self).__init__()
        self.merge(initial_dict)

    def merge(self, override=None):
        """
        Args:
            override: dictionary to be merged into the initial_dict
        """
        self.update(dict_merge(self, override))


class BaseJob(IFramework):
    """Base/Generalized implementation of an ETL Job
    """
    def __init__(self, identifier, debug=False, profile=False):

        if debug:
            import pdb
            pdb.set_trace()

        if profile:
            import cProfile
            self.profiler = cProfile.Profile()
            self.profiler.enable()
        else:
            self.profiler = None

        self.identifier = identifier
        self.status = None

        self.started_at = None
        self.stopped_at = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    @property
    def up_time(self):
        """Up-time of the ETL job

        Returns:
            datetime.datetime: the length of time the ETL job
        """
        if isinstance(self.started_at, datetime.datetime):
            if isinstance(self.stopped_at, datetime.datetime):
                return self.stopped_at - self.started_at
            return datetime.datetime.utcnow() - self.started_at
        else:
            return datetime.timedelta(0)

    @property
    def status(self):
        return '[Job: {0}, Up Time: {1}, Status: {2}]'.format(
            self.identifier,
            self.up_time,
            self.status
        )

    def start(self):
        """Start the ETL job
        """
        self.started_at = datetime.datetime.utcnow()
        self.status = STATUS_START
        logger.info(self.status)

    def stop(self):
        """Stop the ETL job
        """
        self.status = STATUS_STOP
        self.stopped_at = datetime.datetime.utcnow()
        logger.info(self.status)
