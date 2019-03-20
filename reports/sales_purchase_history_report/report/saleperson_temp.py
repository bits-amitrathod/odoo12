
from odoo import api, models


class ReportSalesSalespersonWise(models.AbstractModel):
    _name = 'report.sales_purchase_history_report.purchasehistory_temp'

    @api.model
    def get_report_values(self, docids, data=None):
        sale_order_line = self.env['sale.order.line'].browse(docids)
        return {
            'doc_ids': data.get('ids'),
            'doc_model': data.get('model'),
            'data': sale_order_line

        }
