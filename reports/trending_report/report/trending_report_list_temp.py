import logging
from odoo import api, fields, models
from odoo.tools import float_repr
import datetime

log = logging.getLogger(__name__)

class ReportTrendingReportList(models.AbstractModel):
    _name = 'report.trending_report.trendingreportlist_temp_test'
    _description = "Report Trending ReportList"

    @api.model
    def _get_report_values(self, docids, data=None):

        popup = self.env['popup.trending.report'].search([('create_uid', '=', self._uid)], limit=1, order="id desc")

        return {'data': self.env['res.partner'].browse(docids),'start_date': popup.start_date, 'code': popup.code}