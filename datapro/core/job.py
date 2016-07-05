# -*- coding: utf-8 -*-

import logging

from datapro import BaseJob


logger = logging.getLogger(__name__)


class EtlJob(BaseJob):

    def start(self):
        super(EtlJob, self).start()

    def stop(self):
        super(EtlJob, self).stop()
        # if profiler exists then lets do something about it
