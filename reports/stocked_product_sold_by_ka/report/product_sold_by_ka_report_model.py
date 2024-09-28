import logging
from odoo import api, fields, models
from datetime import datetime

log = logging.getLogger(__name__)


class ReportProductSoldByKa(models.AbstractModel):
    _name = 'report.stocked_product_sold_by_ka.product_sold_by_ka_template'
    _description = "Report Product Sold By Ka"

    @api.model
    def _get_report_values(self, docids, data=None):
        records = self.env['report.product.sold.by.ka'].browse(docids)

        popup = self.env['popup.product.sold.by.ka'].search([('create_uid', '=', self._uid)], limit=1, order="id desc")
        if popup.compute_at_date:
            date = datetime.strptime(str(popup.start_date), '%Y-%m-%d').strftime('%m/%d/%Y') + " - " + datetime.strptime(
                str(popup.end_date), '%Y-%m-%d').strftime('%m/%d/%Y')
        else:
            date = False

        return {'sales': records, 'date': date}
