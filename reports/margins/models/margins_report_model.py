# -*- coding: utf-8 -*-
import datetime

from odoo import api, fields, models, tools
import logging
import odoo.addons.decimal_precision as dp
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

_logger = logging.getLogger(__name__)


class MarginsReport(models.Model):
    _name = "margins"
    _description = "Margins Report"
    _auto = False

    name = fields.Char(string="Name")
    qty = fields.Float(string="Qty",digits='Product Unit of Measure')
    product_id = fields.Many2one('product.product', string='Product',)
    partner_id = fields.Many2one('res.partner', string='Customer',)
    order_id = fields.Many2one('sale.order', string='Order #', )
    sku_code = fields.Char(string="Product SKU")
    unit_price = fields.Float(string="Unit Price")
    unit_cost = fields.Float(string="Unit Cost")
    total_unit_price = fields.Float(string="Total Price")
    total_unit_cost = fields.Float(string="COGS")
    margin = fields.Float(string="Margins")
    margin_percentage = fields.Float(string="Margins %", group_operator='avg')
    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')
    group_by = fields.Char()
    currency_id = fields.Many2one("res.currency", string="Currency",
                                   readonly=True)

    #  @api.model_cr
    def init(self):
        self.init_table()

    def init_table(self):

        tools.drop_view_if_exists(self._cr, 'margins')

        partner_id = self.env.context.get('partner_id')
        product_id = self.env.context.get('product_id')
        sale_order_id = self.env.context.get('sale_order_id')
        s_date = self.env.context.get('s_date')
        e_date = self.env.context.get('e_date')
        group_by = self.env.context.get('group_by')

        select_query = """ SELECT ol.id as id, 
        CONCAT(o.name, ' - [', t.sku_code , '] ' , t.name) as name, 
        ol.product_id as product_id, 
        t.sku_code as sku_code,
        ol.order_id as order_id,
        ol.product_uom_qty as qty,
        o.partner_id as partner_id,
        ol.price_unit as unit_price,
        ol.purchase_price as unit_cost,
        ol.currency_id as currency_id,
        ol.price_subtotal as total_unit_price,
        (ol.product_uom_qty * ol.purchase_price) as total_unit_cost,
        CASE 
                WHEN ol.purchase_price IS NULL OR TRUNC(ol.purchase_price, 2) = 0.00 
                  THEN  CASE WHEN ol.price_subtotal >= 0 THEN ol.price_subtotal ELSE 0 END
                ELSE CASE  WHEN 0 <=(ol.price_subtotal - (ol.product_uom_qty * ol.purchase_price)) THEN (ol.price_subtotal - (ol.product_uom_qty * ol.purchase_price)) ELSE 0 END
        END as margin, 
        CASE 
                WHEN ol.purchase_price IS NULL OR TRUNC(ol.purchase_price, 2) = 0.00 or TRUNC(ol.product_uom_qty, 2) = 0.00 THEN CASE WHEN ol.price_subtotal <= 0 THEN 0 ELSE 100 END
                ELSE TRUNC(( ol.price_subtotal / (CASE WHEN ((ol.price_subtotal - (ol.product_uom_qty * ol.purchase_price)) = 0) THEN 1 ELSE (ol.price_subtotal - (ol.product_uom_qty * ol.purchase_price)) END ) ), 2)
        END as margin_percentage """\

        if not group_by is None:
            select_query = select_query + ", '" + str(group_by) + "' as group_by "

        from_clause = """ FROM 
            sale_order_line ol INNER JOIN  product_product p ON ol.product_id = p.id
            INNER JOIN sale_order o ON ol.order_id = o.id
            INNER JOIN product_template t ON p.product_tmpl_id = t.id
            LEFT JOIN res_partner r ON o.partner_id = r.id """

        where_clause = " WHERE o.date_order IS NOT NULL "

        AND = " AND "
        date_range = ""
        if not s_date is None:
            select_query = select_query + ", '" + str(s_date) + "' as date_from "
            where_clause = where_clause + AND + " o.date_order >= '" + str(s_date) + "'"

        if not e_date is None:
            select_query = select_query + ", '" + str(e_date) + "' as date_to "
            _logger.info(str(e_date + datetime.timedelta(days=1)))
            where_clause = where_clause + AND + " o.date_order <= '" + str(e_date + datetime.timedelta(days=1)) + "'"
            _logger.info(where_clause)

        if not partner_id is None:
            where_clause = where_clause + AND + " o.partner_id = " + str(partner_id)

        if not product_id is None:
            where_clause = where_clause + AND + " ol.product_id = " + str(product_id)

        if not sale_order_id is None:
            where_clause = where_clause + AND + " ol.order_id = " + str(sale_order_id)

        _logger.info('date_range %r', date_range)

        sql_query = "CREATE VIEW margins AS ( " + select_query + from_clause + where_clause + " )"

        self._cr.execute(sql_query)

    #  @api.model_cr
    def delete_and_create(self):
        self.init_table()
