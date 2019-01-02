from odoo import  tools
import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class ReportInStockReportPopup(models.TransientModel):
    _name = 'popup.report.in.stock.report'

    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')

    partner_id = fields.Many2one('res.partner', string='Customer', )
    user_id = fields.Many2one('res.users', 'Salesperson')
    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse')
    sku_code = fields.Char('Product SKU')

    def open_table(self):
        tree_view_id = self.env.ref('in_stock_report.view_in_stock_report_line_tree').id

        res_model = 'report.in.stock.report'

        action = {
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id, 'tree')],
            'view_mode': 'tree',
            'name': 'In Stock Report',
            'res_model': res_model,
            'domain': [('qty_available','>',0)]
        }

        if self.partner_id.id:
            action["domain"].append(('partner_id', '=', self.partner_id.id))

        if self.user_id.id:
            action["domain"].append(('user_id', '=', self.user_id.id))

        if self.warehouse_id.id:
            action["domain"].append(('warehouse_id', '=', self.warehouse_id.id))

        if self.sku_code:
            action["domain"].append(('sku_code', 'ilike', self.sku_code))

        if self.start_date:
            action["domain"].append(('confirmation_date', '>=', self.start_date))

        if self.end_date:
            action["domain"].append(('confirmation_date', '<=', self.end_date))

        return action


class ReportInStockReport(models.Model):
    _name = 'report.in.stock.report'
    _auto = False

    _inherits = {'product.template': 'product_tmpl_id'}


    partner_id = fields.Many2one('res.partner', string='Customer', )
    user_id = fields.Many2one('res.users', 'Salesperson', readonly=True)
    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse')
    product_brand_id = fields.Many2one(
        'product.brand',
        string='Manufacture',
        help='Select a Manufacture for this product'
    )
    product_id = fields.Many2one('product.product', string='Product', )
    product_tmpl_id = fields.Many2one('product.template', 'Product Template')

    min_expiration_date = fields.Date("Min Expiration Date", compute='_calculate_max_min_lot_expiration')
    max_expiration_date = fields.Date("Max Expiration Date", store=False)

    confirmation_date = fields.Date('Confirmation Date')

    @api.multi
    def _calculate_max_min_lot_expiration(self):
        for record in self:
            self.env.cr.execute(
                "SELECT min(use_date), max (use_date) FROM stock_production_lot where product_id = %s",
                (record.product_id.id,))
            query_result = self.env.cr.dictfetchone()
            record.min_expiration_date = fields.Date.from_string(query_result['min'])
            record.max_expiration_date = fields.Date.from_string(query_result['max'])

    @api.model_cr
    def init(self):
        self.init_table()

    def init_table(self):
        tools.drop_view_if_exists(self._cr, self._name.replace(".", "_"))
        sql_query = """
            SELECT
                ROW_NUMBER () OVER (ORDER BY sale_order.partner_id) as id,
                sale_order.partner_id,
                sale_order.user_id,
                sale_order.confirmation_date,
                product_template.product_brand_id,
                product_product.id  AS product_id,
                product_template.id AS product_tmpl_id,
                sale_order.warehouse_id,
                null as min_expiration_date,
                null as max_expiration_date
            FROM
                sale_order
            INNER JOIN
                sale_order_line
            ON
                (
                    sale_order.id = sale_order_line.order_id)
            INNER JOIN
                stock_picking
            ON
                (
                    sale_order.id = stock_picking.sale_id)
            INNER JOIN
                product_product
            ON
                (
                    sale_order_line.product_id = product_product.id)
            INNER JOIN
                product_template
            ON
                (
                    product_product.product_tmpl_id = product_template.id)
            WHERE
                stock_picking.state = 'done' """

        sql_query = "CREATE VIEW " + self._name.replace(".", "_") + " AS ( " + sql_query + " )"
        self._cr.execute(sql_query)

    @api.model_cr
    def delete_and_create(self):
        pass


class ReportPrintInStockReport(models.AbstractModel):
    _name = 'report.in_stock_report.in_stock_report_print'

    @api.model
    def get_report_values(self, docids, data=None):
        return {'data': self.env['report.in.stock.report'].browse(docids)}
