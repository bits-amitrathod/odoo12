from odoo import api, fields, models ,_
import datetime

class ReportSaleOrdersGroupbyProduct(models.TransientModel):
    _name = 'report.sale.orders.groupby.product'
    _description = 'Sales Orders Group by product'
    # _inherits = {'sale.order': 'sale_order_id'}
    # _auto = False
    # _log_access = True

    compute_at_date = fields.Selection([
        (0, 'Show All '),
        (1, 'Date Range ')
    ], string="Compute", help="Choose to analyze the Show Summary or from a specific date in the past.")
    start_date = fields.Datetime('Start Date', help="Choose report Start date", default = (fields.date.today() - datetime.timedelta(days = 31)))
    end_date = fields.Datetime('End Date', help="Choose report End date",
                           default = fields.Datetime.now)

    def open_table(self):

        tree_view_id = self.env.ref('sale.view_order_line_tree').id
        form_view_id = self.env.ref('report_sale_orders_groupby_product.view_sales_order_line_view_cstm').id

        action = {
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'view_type': 'form',
            'view_mode': 'tree,form',
            'name': _('Gross Sales By Product'),
            'res_model': 'sale.order.line',
            'context': {'search_default_product': 1},
        }

        if self.compute_at_date:
            action.update({'domain': [('order_id.confirmation_date', '>=', self.start_date), ('order_id.confirmation_date', '<=', self.end_date),
                   ('state', 'in', ('sale', 'done'))]})
            return action
        else:
            return action
