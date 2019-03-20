
from odoo import api, models


class ReportPurchaseSalespersonWise(models.AbstractModel):
    _name = 'report.inventory_adjustment_report.adjustment_report1'

    @api.model
    def get_report_values(self, docids, data=None):
        purchase_orders = self.env['stock.inventory'].browse(docids)
        return {
            'doc_ids': data.get('ids'),
            'doc_model': data.get('model'),
            'data': purchase_orders,
        }