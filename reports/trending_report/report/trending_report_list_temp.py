import logging
from odoo import api, fields, models
from odoo.tools import float_repr
import datetime

log = logging.getLogger(__name__)

class ReportTrendingReportList(models.AbstractModel):
    _name = 'report.trending_report.trendingreportlist_temp_test'
    @api.model
    def get_report_values(self, docids, data=None):
         return {'data': self.env['res.partner'].browse(docids)}