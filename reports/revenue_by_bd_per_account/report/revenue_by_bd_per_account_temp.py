import logging
from odoo import api, fields, models
from datetime import datetime

log = logging.getLogger(__name__)

class ReportBdRevenuePerAccount(models.AbstractModel):
    _name = 'report.revenue_by_bd_per_account.bd_revenue_pa_temp_test'
    _description = "Report Bd Revenue Per Account"

    @api.model
    def _get_report_values(self, docids, data=None):
        records = self.env['report.bd.revenue.per.account'].browse(docids)

        popup = self.env['popup.bd.revenue.per.account'].search([('create_uid', '=', self._uid)], limit=1, order="id desc")

        if popup.compute_at_date:
            date = datetime.strptime(str(popup.start_date), '%Y-%m-%d').strftime(
                '%m/%d/%Y') + " - " + datetime.strptime(
                str(popup.end_date), '%Y-%m-%d').strftime('%m/%d/%Y')
        else:
            date = False

        return {'sales': records, 'date': date}
