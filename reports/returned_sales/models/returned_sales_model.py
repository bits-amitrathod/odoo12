# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools
import logging

_logger = logging.getLogger(__name__)


class ReturnrdSales(models.Model):
    _name = "returned_sales.order"
    _auto = False

    name = fields.Char("Order #")
    order_id = fields.Many2one('sale.order', string='Order', )
    cost_price = fields.Float("Qty Ordered")
    done_qty = fields.Float("Qty")
    partner_id = fields.Many2one('res.partner', string='Customer', )
    product_id = fields.Many2one('product.product', string='Product', )
    move_id = fields.Many2one('stock.move', string='Stock Move', ),
    moved_date = fields.Datetime('Date')
    user_id = fields.Many2one('res.users', 'Salesperson', readonly=True)
    sku_code = fields.Char('SKU / Catalog No')

    @api.model_cr
    def init(self):
        self.init_table()

    def init_table(self):
        tools.drop_view_if_exists(self._cr, 'returned_sales_order')
        #        sql_query = """ CREATE VIEW returned_sales_order AS ( SELECT ROW_NUMBER () OVER (ORDER BY move_id) as id, concat('ROO','') as name, so.id as order_id, m.id as move_id, m.partner_id as partner_id, m.product_id as product_id, m.product_uom_qty as done_qty, (sl.price_unit * m.product_uom_qty) as cost_price
        # FROM stock_move m INNER JOIN stock_move_line ml
        # ON m.id = ml.move_id
        # INNER JOIN sale_order_line sl ON sl.id = m.sale_line_id
        # INNER JOIN sale_order so ON sl.order_id = so.id
        # WHERE m.sale_line_id IS NOT NULL AND m.origin_returned_move_id IS NOT NULL AND m.state = 'done' AND m.scrapped IS FALSE
        #                """

        sql_query = """  CREATE VIEW returned_sales_order AS ( 
                    SELECT ROW_NUMBER () OVER (ORDER BY move_id) as id, concat(so.name,' - ', t.name) as name, 
                    so.id as order_id, m.id as move_id, so.user_id, t.sku_code,
                    m.partner_id as partner_id, m.product_id as product_id, m.product_uom_qty as done_qty, 
                    (sl.price_unit * m.product_uom_qty) as cost_price,
                    m.date as moved_date
                    FROM stock_move m INNER JOIN stock_move_line ml
                    ON m.id = ml.move_id
                    INNER JOIN sale_order_line sl ON sl.id = m.sale_line_id 
                    INNER JOIN sale_order so ON sl.order_id = so.id
                    INNER JOIN product_product p ON p.id = m.product_id
                    INNER JOIN product_template t ON p.product_tmpl_id = t.id
                    WHERE m.sale_line_id IS NOT NULL AND m.origin_returned_move_id IS NOT NULL AND m.state = 'done' 
                    AND m.scrapped IS FALSE """

        partner_id = self.env.context.get('partner_id')
        product_id = self.env.context.get('product_id')
        sales_partner_id = self.env.context.get('sales_partner_id')

        # start_date = self.env.context.get('s_date')
        # end_date = self.env.context.get('e_date')

        AND = " AND "

        if not partner_id is None:
            sql_query = sql_query + AND + " m.partner_id = " + str(partner_id)

        if not product_id is None:
            sql_query = sql_query + AND + " m.product_id = " + str(product_id)

        if not sales_partner_id is None:
            sql_query = sql_query + AND + " ml.owner_id = " + str(sales_partner_id)

        # if not start_date is None and not end_date is None:
        #     sql_query = sql_query + AND + " m.date >= '" + str(start_date) + "'" + AND + "m.date <= '" + str(
        #         end_date) + "'"

        sql_query = sql_query + " )"

        self._cr.execute(sql_query)

    @api.model_cr
    def delete_and_create(self):
        self.init_table()
