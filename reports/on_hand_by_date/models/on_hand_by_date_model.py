# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools
import logging
from datetime import datetime

from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc

_logger = logging.getLogger(__name__)


class OnHandByDate(models.Model):
    _name = "on_hand_by_date.stock"
    _auto = False

    name = fields.Char("Order #")
    qty_on_hand = fields.Float("Qty")
    product_id = fields.Many2one('product.product', string='Product',)
    partner_id = fields.Many2one('res.partner', string='Vendor',)
    sku_code = fields.Char()
    vendor_name = fields.Char()
    report_date = fields.Char()
    costing_method = fields.Integer()
    unit_price = fields.Float("Unit Price", compute='_get_product_price', store=False)
    assets_value = fields.Float("Assets Value", compute='_get_asset_value', store=False)
    currency_id = fields.Many2one('res.currency', string='Currency')

    def _get_product_price(self):
        for record in self:
            # record.currency_id = record.env.user.company_id.currency_id
            _logger.info('currency_id: %r', str(record.currency_id))
            if record.costing_method == 1:
                record.unit_price = record.product_id.product_tmpl_id.standard_price
            elif record.costing_method == 2:
                record.unit_price = record.product_id.product_tmpl_id.standard_price
            elif record.costing_method == 3:
                record.unit_price = record.product_id.product_tmpl_id.standard_price
            record.assets_value = record.unit_price * record.qty_on_hand

    def _get_asset_value(self):
        pass

    @api.model_cr
    def init(self):
        self.init_table()

    def init_table(self):

        tools.drop_view_if_exists(self._cr, 'on_hand_by_date_stock')

        report_date = self.env.context.get('report_date')

        costing_method = self.env.context.get('costing_method')

        if costing_method is None:
            costing_method = 0

        if report_date is None:
            report_date = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        include_zero_quantities = self.env.context.get('include_zero_quantities')

        if not include_zero_quantities is None and include_zero_quantities:
            include_zero_quantities = " FULL JOIN "
        else:
            include_zero_quantities = " INNER JOIN "

        sql_query = """  CREATE VIEW on_hand_by_date_stock AS ( 
        SELECT  
            ROW_NUMBER () OVER (ORDER BY product_id) as id, p.id as product_id, c.currency_id as currency_id, 
            q.qty_on_hand, b.name as vendor_name, t.name as name, """ + str(costing_method) + """ as costing_method,
            0.0 as assets_value, 0.0 as unit_price,
            t.sku_code as sku_code, b.partner_id as partner_id, '""" + str(report_date) + """' as report_date
        FROM (
                SELECT 
                    sq.product_id as product_id, SUM(sq.quantity) as qty_on_hand, sq.company_id as company_id
                FROM 
                    stock_quant sq LEFT JOIN stock_production_lot l ON sq.lot_id = l.id LEFT JOIN stock_location lc 
                ON 
                    lc.id = sq.location_id 
                WHERE 
                    (lc.create_date <= '""" + str(report_date) + """' AND l.create_date <= '""" + str(report_date) + """') 
                    AND sq.company_id IS NOT NULL AND
                    sq.quantity >= 0 AND l.use_date >= '""" + str(report_date) + """'  
                    GROUP BY (sq.product_id, sq.company_id) 
            ) q """ + include_zero_quantities + """ 
            product_product p ON p.id = q.product_id
        LEFT JOIN 
            product_template t ON t.id = p.product_tmpl_id
        LEFT JOIN 
            product_brand b ON b.id = t.product_brand_id 
        LEFT JOIN res_company c ON c.id = q.company_id                   
        WHERE 
            p.create_date <= '""" + str(report_date) + "' "

        partner_id = self.env.context.get('partner_id')
        product_id = self.env.context.get('product_id')

        AND = " AND "

        if not partner_id is None:
            sql_query = sql_query + AND + " b.partner_id = " + str(partner_id)

        if not product_id is None:
            sql_query = sql_query + AND + " q.product_id = " + str(product_id)

        sql_query = sql_query + " )"

        self._cr.execute(sql_query)

    @api.model_cr
    def delete_and_create(self):
        self.init_table()