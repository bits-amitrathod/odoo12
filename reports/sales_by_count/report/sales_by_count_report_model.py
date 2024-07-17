import logging
from odoo import api, fields, models
from datetime import datetime

log = logging.getLogger(__name__)


class ReportProductSaleByCount(models.AbstractModel):
    _name = 'report.sales_by_count.sales_by_count_template'
    _description = "Report Product Sale By Count"

    def _get_report_values(self, docids, data=None):
        records = self.env['report.sales.by.count'].browse(docids)

        popup = self.env['popup.sales.by.count'].search([('create_uid', '=', self._uid)], limit=1, order="id desc")
        if popup.compute_at_date:
            date = datetime.strptime(str(popup.start_date), '%Y-%m-%d').strftime('%m/%d/%Y') + " - " + datetime.strptime(
                str(popup.end_date), '%Y-%m-%d').strftime('%m/%d/%Y')
        else:
            date = False

        return {'sales': records, 'date': date}
