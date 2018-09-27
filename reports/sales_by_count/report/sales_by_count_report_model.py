import logging
from odoo import api, fields, models

log = logging.getLogger(__name__)


class ReportProductSaleByCount(models.AbstractModel):
    _name = 'report.sales_by_count.sales_by_count_template'

    @api.model
    def get_report_values(self, docids, data=None):
        records = self.env['product.product'].browse(docids)
        return {
            'data': records.sorted(key=lambda r: r.total_sale_qty, reverse=True)}
