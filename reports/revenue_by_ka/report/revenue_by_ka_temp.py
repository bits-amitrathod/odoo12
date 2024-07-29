import logging
from odoo import api, fields, models
from datetime import datetime
import calendar
log = logging.getLogger(__name__)

class ReportKaRevenue(models.AbstractModel):
    _name = 'report.revenue_by_ka.ka_revenue_temp_test'
    _description = "Report Ka Revenue"

    @api.model
    def _get_report_values(self, docids, data=None):
        records = self.env['report.ka.revenue'].browse(docids)

        popup = self.env['popup.ka.revenue'].search([('create_uid', '=', self._uid)], limit=1, order="id desc")

        if popup.start_year:
            start_date = datetime.strptime(str(popup.start_year) + "-" + str(popup.start_month) + "-01",
                                                    "%Y-%m-%d").date()

            end_date_custom = datetime.strptime(str(popup.end_year) + "-" + str(popup.end_month) + "-15",
                                                         "%Y-%m-%d")

            end_date = datetime(end_date_custom.year, end_date_custom.month,
                                         calendar.mdays[end_date_custom.month]).date()

            date = datetime.strptime(str(start_date), '%Y-%m-%d').strftime(
                '%m/%d/%Y') + " - " + datetime.strptime(
                str(end_date), '%Y-%m-%d').strftime('%m/%d/%Y')
        else:
            date = False

        return {'sales': records, 'date': date}
