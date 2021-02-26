# -*- coding: utf-8 -*-

from odoo import models, api
import logging
import os,shutil
from datetime import datetime
from dateutil.relativedelta import relativedelta
import errno

_logger = logging.getLogger(__name__)

#path = os.path.abspath(__file__)
#dir_path = os.path.dirname(os.path.dirname(os.path.dirname(path)))
#UPLOAD_DIR = dir_path + "/Documents/uploads/"
UPLOAD_DIR = "/home/odoo/Documents/uploads/"


class RemoveDocumentScheduler(models.Model):
    _name = 'remove.document.cron.scheduler'

    @api.model
    #@api.multi
    def process_remove_document_scheduler(self):
        _logger.info('In Remove document Scheduler')

        interval_number_of_days = 30

        for x in range(interval_number_of_days):
            temp = (datetime.today() + relativedelta(days=+int(-30 - x)))

            directory_path = UPLOAD_DIR + str(temp.strftime("%d%m%Y"))

            _logger.info('directory_path : '+str(directory_path))

            if directory_path != "/" and os.path.isdir(directory_path):
                _logger.info('directory exist')
                try:
                    shutil.rmtree(directory_path, ignore_errors=True, onerror=None)
                except OSError as exc:
                    if exc.errno != errno.EEXIST:
                        raise
            else:
                _logger.info('directory does not exist')