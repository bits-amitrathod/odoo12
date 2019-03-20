
from odoo import api, models


class ReportPurchaseSalespersonWise(models.AbstractModel):
    _name = 'report.rma_report.purchase_report'

    @api.model
    def get_report_values(self, docids, data=None):
        purchase_orders = self.env['stock.picking'].browse(docids)

        action= {
            'doc_ids': data.get('ids'),
            'doc_model': data.get('model'),
            'data': purchase_orders,
        }
        action.update({'target': 'main'})
        return action
