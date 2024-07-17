from odoo import tools
import logging
import datetime
from odoo.addons import decimal_precision as dp
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class ReportInStockReportPopup(models.TransientModel):
    _name = 'popup.report.in.stock.report'
    _description = "Report In Stock Report Popup"

    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')

    partner_id = fields.Many2one('res.partner', string='Customer', )
    user_id = fields.Many2one('res.users', 'Business Development')
    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse')
    sku_code = fields.Many2one('product.product', string='Product SKU',
                               domain="[('active','=',True),('product_tmpl_id.type','=','product')]")
    saleforce_ac = fields.Char("Parent SF A/C  No#")

    def open_table(self):
        tree_view_id = self.env.ref('in_stock_report.view_in_stock_report_line_tree').id
        margins_context = {'start_date': self.start_date,'end_date':self.end_date}
        res_model = 'report.in.stock.report'
        self.env[res_model].with_context(margins_context).delete_and_create()

        if self.saleforce_ac:
            action = {
                'type': 'ir.actions.act_window',
                'views': [(tree_view_id, 'tree')],
                'view_mode': 'tree',
                'name': 'In Stock Report',
                'res_model': res_model,
                'context': margins_context,
                'domain': ['|', ('partner_id.parent_id.saleforce_ac', '=', self.saleforce_ac),
                           ('partner_id.saleforce_ac', '=', self.saleforce_ac),
                           ('actual_quantity', '>', 0)]
            }
        else:
            action = {
                'type': 'ir.actions.act_window',
                'views': [(tree_view_id, 'tree')],
                'view_mode': 'tree',
                'name': 'In Stock Report',
                'res_model': res_model,
                'context':margins_context,
                'domain': [('actual_quantity','>',0)]
            }

        if self.partner_id.id:
            action["domain"].append(('partner_id', '=', self.partner_id.id))

        if self.user_id.id:
            action["domain"].append(('user_id', '=', self.user_id.id))

        if self.warehouse_id.id:
            action["domain"].append(('warehouse_id', '=', self.warehouse_id.id))

        if self.sku_code:
            action["domain"].append(('product_id.id', 'ilike', self.sku_code.id))

        return action


class ReportInStockReport(models.Model):
    _name = 'report.in.stock.report'
    _description = "Report InStock Report"

    _auto = False

    _inherits = {'product.template': 'product_tmpl_id'}


    partner_id = fields.Many2one('res.partner', string='Customer', )
    user_id = fields.Many2one('res.users', 'Business Development', readonly=True)
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
    price_list=fields.Float("Sales Price",  compute='_calculate_max_min_lot_expiration')
    # actual_quantity = fields.Float(string='Qty Available For Sale', compute='_calculate_max_min_lot_expiration', digits=dp.get_precision('Product Unit of Measure'))
    partn_name=fields.Char()

    #@api.multi
    def _calculate_max_min_lot_expiration(self):
        for record in self:
            record.actual_quantity = record.product_tmpl_id.actual_quantity
            if record.partner_id.property_product_pricelist.id:
                a = record.partner_id.property_product_pricelist._get_product_price(record.product_id, record.actual_quantity)
                if a:
                    record.price_list =a
                else:
                    record.price_list = None
            else:
                record.price_list = 0

            self.env.cr.execute(
                """
                SELECT
                sum(quantity), min(use_date), max(use_date)
            FROM
                stock_quant
            INNER JOIN
                stock_lot
            ON
                (
                    stock_quant.lot_id = stock_lot.id)
            INNER JOIN
                stock_location
            ON
                (
                    stock_quant.location_id = stock_location.id)
            WHERE
                stock_location.usage in('internal', 'transit') and stock_lot.product_id  = %s
                """,
                (record.product_id.id,))
            query_result = self.env.cr.dictfetchone()
            record.min_expiration_date = fields.Date.from_string(query_result['min'])
            record.max_expiration_date = fields.Date.from_string(query_result['max'])

    #  @api.model_cr
    def init(self):
        self.init_table()

    def init_table(self):
        tools.drop_view_if_exists(self._cr, self._name.replace(".", "_"))
        s_date = self.env.context.get('start_date')
        e_date = self.env.context.get('end_date')

        sql_query = """
            SELECT  DISTINCT on (partn_name)
             CONCAT(sale_order.partner_id, product_product.id) as partn_name,
             ROW_NUMBER () OVER (ORDER BY sale_order.partner_id) as id,
            sale_order.partner_id,
            sale_order.user_id,
            product_template.product_brand_id,
            product_product.id AS product_id,
            product_template.id AS product_tmpl_id,
            product_template.actual_quantity,
            sale_order.warehouse_id,
            null as price_list,
            null as min_expiration_date,
            null as max_expiration_date
            FROM
            sale_order
            INNER JOIN
            sale_order_line
            ON(
            sale_order.id = sale_order_line.order_id)
            INNER JOIN
            product_product
            ON
            (
            sale_order_line.product_id = product_product.id)
            INNER JOIN
            product_template
            ON
            (
            product_product.product_tmpl_id = product_template.id  and  product_template.sale_ok = True)
            
            """
        groupby  = """
         group by partn_name, public.sale_order.partner_id,
                public.sale_order.user_id,
                public.product_template.product_brand_id,
                public.product_product.id  ,
                public.product_template.id ,
                public.sale_order.warehouse_id
                """
        if s_date and e_date and not s_date is None and not e_date is None:
            e_date = datetime.datetime.strptime(str(e_date), "%Y-%m-%d")
            e_date = e_date + datetime.timedelta(days=1)
            sql_query=sql_query+""" and sale_order.state in ('sale','sent') and sale_order.date_order>=%s  and sale_order.date_order<=%s"""
            sql_query = "CREATE VIEW " + self._name.replace(".", "_") + " AS ( " + sql_query + groupby + " )"
            self._cr.execute(sql_query, (str(s_date), str(e_date)))
        else:
            sql_query = "CREATE VIEW " + self._name.replace(".", "_") + " AS ( " + sql_query +  groupby +" )"
            self._cr.execute(sql_query)

    #  @api.model_cr
    def delete_and_create(self):
        self.init_table()


class ReportPrintInStockReport(models.AbstractModel):
    _name = 'report.in_stock_report.in_stock_report_print'
    _description = "Report Print InStock Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        dates_picked = self.env['popup.report.in.stock.report'].search([('create_uid', '=', self._uid)], limit=1,
                                                                       order="id desc")

        return {'dateRange': dates_picked, 'data': self.env['report.in.stock.report'].browse(docids)}
