from odoo import api, fields, models, tools
from odoo.osv import osv
import warnings
from odoo.exceptions import UserError, ValidationError
import logging

from odoo import models, fields, api
import datetime

_logger = logging.getLogger(__name__)


class ReportInStockReportPopup(models.TransientModel):
    _name = 'popup.report.in.stock.report'

    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')

    partner_id = fields.Many2one('res.partner', string='Customer', )
    user_id = fields.Many2one('res.users', 'Salesperson')
    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse')
    sku_code = fields.Char('SKU / Catalog No')

    def open_table(self):
        tree_view_id = self.env.ref('in_stock_report.view_in_stock_report_line_tree').id

        res_model = 'report.in.stock.report'
        self.env[res_model].delete_and_create()

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


class ReportInStockReport(models.TransientModel):
    _name = 'report.in.stock.report'

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

    min_expiration_date = fields.Date("Min Expiration Date", compute='_calculate_sku')
    max_expiration_date = fields.Date("Max Expiration Date")

    confirmation_date = fields.Date('Confirmation Date')

    @api.multi
    def _calculate_sku(self):
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
        sql_query = """ 
                    TRUNCATE TABLE """ + self._name.replace(".", "_") + """
                    RESTART IDENTITY;
                """
        self._cr.execute(sql_query)

        sql_query = """ 
        INSERT INTO """ + self._name.replace(".", "_") + """  (partner_id,user_id,confirmation_date, product_brand_id, product_id,product_tmpl_id,warehouse_id)
            SELECT
                public.sale_order.partner_id,
                public.sale_order.user_id,
                public.sale_order.confirmation_date,
                public.product_template.product_brand_id,
                public.product_product.id  AS product_id,
                public.product_template.id AS product_tmpl_id,
                public.sale_order.warehouse_id
            FROM
                public.sale_order
            INNER JOIN
                public.sale_order_line
            ON
                (
                    public.sale_order.id = public.sale_order_line.order_id)
            INNER JOIN
                public.stock_picking
            ON
                (
                    public.sale_order.id = public.stock_picking.sale_id)
            INNER JOIN
                public.product_product
            ON
                (
                    public.sale_order_line.product_id = public.product_product.id)
            INNER JOIN
                public.product_template
            ON
                (
                    public.product_product.product_tmpl_id = public.product_template.id)
            WHERE
                public.stock_picking.state = 'done' ; """

        self._cr.execute(sql_query)

    @api.model_cr
    def delete_and_create(self):
        self.init_table()


class ReportPrintInStockReport(models.AbstractModel):
    _name = 'report.in_stock_report.in_stock_report_print'

    @api.model
    def get_report_values(self, docids, data=None):
        return {'data': self.env['report.in.stock.report'].browse(docids)}
