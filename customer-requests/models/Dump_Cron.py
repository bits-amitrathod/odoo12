# -*- coding: utf-8 -*-

from odoo import models, api
import logging
import time

_logger = logging.getLogger(__name__)



class DumpDiscussCron(models.Model):
    _name = 'dump.discuss.cron.scheduler'

    @api.model
    @api.multi
    def process_dump_discuss_scheduler(self):
        _logger.info('In Dump Discuss Data Scheduler')

        try:
            start_time = time.time()
            _logger.info('Dump Cron Stat Time : ')
            _logger.info(start_time)

            self.env['mail.message'].DumpData()

            end_time = time.time()
            _logger.info('Dump Cron End Time : ')
            _logger.info(end_time)
            _logger.info('***********Required time for processing Dump Cron...(In Seconds)********')
            _logger.info(end_time - start_time)

        except Exception as exc:
            _logger.error("Error In Dumping Discuss Data %r", exc)
