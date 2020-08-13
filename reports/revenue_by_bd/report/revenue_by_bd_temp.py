import logging
from odoo import api, fields, models
from datetime import datetime

log = logging.getLogger(__name__)

class ReportBdRevenue(models.AbstractModel):
    _name = 'report.revenue_by_bd.bd_revenue_temp_test'

    @api.model
    def _get_report_values(self, docids, data=None):
        records = self.env['report.bd.revenue'].browse(docids)

        popup = self.env['popup.bd.revenue'].search([('create_uid', '=', self._uid)], limit=1, order="id desc")

        if popup.start_date and popup.end_date:
            date = datetime.strptime(str(popup.start_date), '%Y-%m-%d').strftime(
                '%m/%d/%Y') + " - " + datetime.strptime(
                str(popup.end_date), '%Y-%m-%d').strftime('%m/%d/%Y')
        else:
            date = False

        return {'sales': records, 'date': date}

    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(str(date_string), DEFAULT_SERVER_DATE_FORMAT).date()
