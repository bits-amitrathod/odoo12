
from odoo import api, fields, models,_


class SaleSalespersonReport(models.TransientModel):
    _name = 'sale.purchase.history.report'

    start_date = fields.Date('Start Date', required=True)
    end_date = fields.Date(string="End Date", required=True)
    product_id = fields.Many2many('product.product', string="Products")
    order_partner_id = fields.Many2one('res.partner', string='Customer')

    @api.multi
    def open_table(self):
        tree_view_id = self.env.ref('sales_purchase_history_report.list_view').id
        form_view_id = self.env.ref('sales_purchase_history_report.view_sales_order_line_view_cstm').id

        action = {
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'view_mode': 'tree,form',
            'name': _('Sales Purchase History'),
            'res_model': 'sale.order.line',
            'domain': [('create_date', '>=', self.start_date), ('create_date', '<=', self.end_date), ('state', '!=', 'cancel')],
            'target': 'main'
        }

        if self.product_id and self.order_partner_id:
            action['domain'].append(('product_id', '=', self.product_id.id))
            action['domain'].append(('order_partner_id', '=', self.order_partner_id.id))
        elif self.product_id:
            action['domain'].append(('product_id', '=', self.product_id.id))
        elif self.order_partner_id:
            action['domain'].append(('order_partner_id', '=', self.order_partner_id.id))
        return action