
from odoo import api, models
from datetime import datetime


class ReportPurchaseSalespersonWise(models.AbstractModel):
    _name = 'report.purchase_history_custome.purchase_report'


    @api.model
    def get_report_values(self, docids, data=None):
        purchase_orders = self.env['purchase.order.line'].browse(docids)

        popup = self.env['popup.view.model.purchase.history'].search([('create_uid', '=', self._uid)], limit=1, order="id desc")


        date = datetime.strptime(popup.start_date, '%Y-%m-%d').strftime('%m/%d/%Y') + " - " + datetime.strptime(
            popup.end_date, '%Y-%m-%d').strftime('%m/%d/%Y')


        return {
            'doc_ids': data.get('ids'),
            'doc_model': data.get('model'),
            'data': purchase_orders,
            'date': date
        }