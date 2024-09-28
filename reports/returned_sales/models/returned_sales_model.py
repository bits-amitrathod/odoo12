# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools
import logging
import odoo.addons.decimal_precision as dp
_logger = logging.getLogger(__name__)


class ReturnrdSales(models.Model):
    _name = "report.returned.sales.order"
    _description = "Reports Returnrd Sales"
    _auto = False

    name = fields.Char("Sales Order#")
    order_id = fields.Many2one('sale.order', string='Order', )
    cost_price = fields.Float("Qty Ordered")
    done_qty = fields.Float("Qty Done",digits='Product Unit of Measure', required=True)
    product_uom_id = fields.Many2one('uom.uom', 'UOM')
    partner_id = fields.Many2one('res.partner', string='Customer', )
    product_id = fields.Many2one('product.product', string='Product Name', )
    move_id = fields.Many2one('stock.move', string='Stock Move' )
    moved_date = fields.Date('Date')
    user_id = fields.Many2one('res.users', 'Business Development', readonly=True)
    sku_code = fields.Char('Product SKU')
    currency_id = fields.Many2one("res.currency", string="Currency", readonly=True)


    #  @api.model_cr
    def init(self):
        self.init_table()

    def init_table(self):
        tools.drop_view_if_exists(self._cr, self._name.replace(".", "_"))

        select_query = """ 
                    SELECT ROW_NUMBER () OVER (ORDER BY move_id) as id, concat(so.name,' - ', t.name) as name, 
                    so.id as order_id, m.id as move_id, so.user_id, t.sku_code,
                    m.partner_id as partner_id, m.product_id as product_id, ml.qty_done as done_qty, 
                    (sl.price_unit * ml.qty_done) as cost_price,
                    sl.currency_id as currency_id,
                    DATE(m.date) as moved_date,ml.product_uom_id
                    FROM stock_move m INNER JOIN stock_move_line ml
                    ON m.id = ml.move_id
                    INNER JOIN sale_order_line sl ON sl.id = m.sale_line_id 
                    INNER JOIN sale_order so ON sl.order_id = so.id
                    INNER JOIN product_product p ON p.id = m.product_id
                    INNER JOIN product_template t ON p.product_tmpl_id = t.id
                    WHERE m.sale_line_id IS NOT NULL AND m.origin_returned_move_id IS NOT NULL AND m.state = 'done' 
                    AND m.scrapped IS FALSE """

        sql_query = "CREATE VIEW " + self._name.replace(".", "_") + " AS ( " + select_query + " )"
        self._cr.execute(sql_query)

    #  @api.model_cr
    def delete_and_create(self):
        self.init_table()
