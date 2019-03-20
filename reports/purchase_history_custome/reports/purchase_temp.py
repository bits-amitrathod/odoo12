
from odoo import api, models


class ReportPurchaseSalespersonWise(models.AbstractModel):
    _name = 'report.purchase_history_custome.purchase_report'


    @api.model
    def get_report_values(self, docids, data=None):
        purchase_orders = self.env['purchase.order'].browse(docids)
        return {
            'doc_ids': data.get('ids'),
            'doc_model': data.get('model'),
            'data': purchase_orders,
        }