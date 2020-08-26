import logging
from odoo import api, fields, models
from datetime import datetime
import calendar
log = logging.getLogger(__name__)

class ReportKaRevenue(models.AbstractModel):
    _name = 'report.revenue_by_ka.ka_revenue_temp_test'

    @api.model
    def _get_report_values(self, docids, data=None):
        records = self.env['report.ka.revenue'].browse(docids)

        popup = self.env['popup.ka.revenue'].search([('create_uid', '=', self._uid)], limit=1, order="id desc")

        if popup.start_date:
            start_date_month = datetime(popup.start_date.year, popup.start_date.month, 1).date()
            end_date_month = datetime(popup.start_date.year, popup.start_date.month,
                                           calendar.mdays[popup.start_date.month]).date()

            date = datetime.strptime(str(start_date_month), '%Y-%m-%d').strftime(
                '%m/%d/%Y') + " - " + datetime.strptime(
                str(end_date_month), '%Y-%m-%d').strftime('%m/%d/%Y')
        else:
            date = False

        return {'sales': records, 'date': date}
