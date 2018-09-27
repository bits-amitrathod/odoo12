import logging
from odoo import api, fields, models

log = logging.getLogger(__name__)


class ReportProductsOnOrder(models.AbstractModel):
    _name = 'report.products_on_order.prod_on_order_temp'

    @api.model
    def get_report_values(self, docids, data=None):
        records = self.env['res.partner'].browse(docids)
        return {
            'data': records}
