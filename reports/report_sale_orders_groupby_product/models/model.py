from odoo import api, fields, models ,_
import datetime

class ReportSaleOrdersGroupbyProduct(models.TransientModel):
    _name = 'popup.sale.orders.groupby.product.report'
    _description = 'Sales Orders Group by product'
    # _inherits = {'sale.order': 'sale_order_id'}
    # _auto = False
    # _log_access = True

    compute_at_date = fields.Selection([
        (0, 'Show All '),
        (1, 'Date Range ')
    ], string="Compute", help="Choose to analyze the Show Summary or from a specific date in the past.")
    start_date = fields.Date('Start Date', help="Choose report Start date", default = (fields.date.today() - datetime.timedelta(days = 31)))
    end_date = fields.Date('End Date', help="Choose report End date",
                           default = fields.date.today())

    def open_table(self):

        tree_view_id = self.env.ref('report_sale_orders_groupby_product.report_sale_orders_group_by_product_tree').id
        form_view_id = self.env.ref('report_sale_orders_groupby_product.view_sales_order_line_view_cstm').id

        action = {
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'view_type': 'form',
            'view_mode': 'tree,form',
            'name': _('Gross Sales By Product'),
            'res_model': 'sale.order.line',
            'context': {'search_default_product': 1},
            'domain': [('state', 'in', ['sale', 'done']),('qty_delivered', '>',0)]
        }

        if self.compute_at_date:
            action.update({'domain': [('order_id.date_order', '>=', self.start_date), ('order_id.date_order', '<=', self.end_date),
                   ('state', 'in', ('sale', 'done')),('qty_delivered', '>',0)]})
            return action
        else:
            return action


class ReportSaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

     # Below line is commented due to sales order duplicate exception
    # _inherits = {'sale.order': 'order_id'}
    order_id = fields.Many2one('sale.order', string='Order Reference')
    date_order = fields.Datetime('Order Date', compute='_compute_date_order', store=False)
    sku_code = fields.Char('Product SKU', store=False, compute="_get_sku")

    @api.multi
    def _get_sku(self):
        for order in self:
                order.sku_code = order.product_id.product_tmpl_id.sku_code

    @api.multi
    def _compute_date_order(self):
        for order in self:
            order.date_order = order.order_id.date_order


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.multi
    def action_view_sales(self):
        tree_view_id = self.env.ref('report_sale_orders_groupby_product.report_sale_orders_group_by_product_tree').id
        pivote_view_id = self.env.ref('report_sale_orders_groupby_product.view_sold_level_pivot').id
        product = self.env['product.product'].search([('product_tmpl_id', 'in', self.ids)])
        action = {
            'name': 'Sales by Channel',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,pivot',
            'views': [(tree_view_id, 'tree'),(pivote_view_id, 'pivot')],
            'res_model': 'sale.order.line',
            'domain': [('product_id', 'in', product.ids)]
        }
        return action

    @api.multi
    def action_view_po(self):
        tree_view_id = self.env.ref('purchase.purchase_order_line_tree').id
        pivote_view_id = self.env.ref('report_sale_orders_groupby_product.view_prchase_level_pivot').id
        product = self.env['product.product'].search([('product_tmpl_id', 'in', self.ids)])
        action = {
            'name': 'Purchase by Channel',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,pivot',
            'views': [(tree_view_id, 'tree'),(pivote_view_id, 'pivot')],
            'res_model': 'purchase.order.line',
            'domain': [('product_id', 'in', product.ids)]
        }
        return action


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.multi
    def action_view_sales(self):
        tree_view_id = self.env.ref('report_sale_orders_groupby_product.report_sale_orders_group_by_product_tree').id
        pivote_view_id = self.env.ref('report_sale_orders_groupby_product.view_sold_level_pivot').id
        action = {
                'name': 'Sales by Channel',
                'type': 'ir.actions.act_window',
                'view_mode': 'tree,pivot',
                'views': [(tree_view_id, 'tree'), (pivote_view_id, 'pivot')],
                'res_model': 'sale.order.line',
                'domain': [('product_id', 'in', self.ids)]
        }
        return action

    @api.multi
    def action_view_po(self):
        tree_view_id = self.env.ref('purchase.purchase_order_line_tree').id
        pivote_view_id = self.env.ref('report_sale_orders_groupby_product.view_prchase_level_pivot').id
        action = {
                'name': 'Purchase by Channel',
                'type': 'ir.actions.act_window',
                'view_mode': 'tree,pivot',
                'views': [(tree_view_id, 'tree'), (pivote_view_id, 'pivot')],
                'res_model': 'purchase.order.line',
                'domain': [('product_id', 'in', self.ids)]
            }
        return action