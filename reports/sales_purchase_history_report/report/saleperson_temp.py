
from odoo import api, models
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)

class ReportSalesSalespersonWise(models.AbstractModel):
    _name = 'report.sales_purchase_history_report.purchasehistory_temp'
    _description = "Report Sales Salesperson Wise"

    @api.model
    def _get_report_values(self, docids, data=None):
        sale_order_line = self.env['sale.order.line'].browse(docids)

        popup = self.env['sale.purchase.history.report'].search([('create_uid', '=', self._uid)], limit=1, order="id desc")

        if popup.start_date and popup.end_date:
            date = datetime.strptime(str(popup.start_date), '%Y-%m-%d').strftime('%m/%d/%Y') + " - " + datetime.strptime(
                str(popup.end_date), '%Y-%m-%d').strftime('%m/%d/%Y')
        else:
            date = False
        for sale_order in sale_order_line:
            _logger.info("sales purchase history %r:",sale_order)
        return {
            'doc_ids': data.get('ids'),
            'doc_model': data.get('model'),
            'data': sale_order_line,
            'date': date
        }
