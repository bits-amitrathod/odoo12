# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools
import logging
import datetime
from datetime import date, datetime

logger = logging.getLogger(__name__)


class aging_report(models.Model):
    _name = 'aging.report'
    _auto = False
    _rec_name = 'product_id'

    # cr_date = fields.Date("Created date")
    qty = fields.Integer("Product Qty", compute='get_quantity_byorm', store=False)
    days = fields.Char("Days", store=False)

    sku_code = fields.Char(string="Product SKU")
    prod_lot_id = fields.Many2one('stock.production.lot', 'stock production lot')
    product_name = fields.Char(string="Product Name")
    lot_name = fields.Char(string="Lot#")
    create_date = fields.Date(string="Created Date")

    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse')
    location_id = fields.Many2one('stock.location', string="Location")
    # tracking  = fields.Char("Tracking" ,compute='_get_Data',default=0)
    warehouse_name = fields.Char(string="Warehouse", store=False)
    product_uom_id = fields.Char(string="UOM", store=False)

    current_date = date.today()
    use_date = fields.Date(string="Expiry Date" ,store=False)
    product_id = fields.Many2one('product.template', 'Product')

    @api.multi
    def get_quantity_byorm(self):
        for order in self:
            order.use_date = order.prod_lot_id.use_date
            order.qty = order.prod_lot_id.product_qty
            order.product_uom_id = order.prod_lot_id.product_id.product_tmpl_id.uom_id.name
            order.warehouse_name = order.warehouse_id.name

        for order in self:
            date_format = "%Y-%m-%d"
            today = date.today().strftime('%Y-%m-%d')
            a = datetime.strptime(today, date_format)
            b = datetime.strptime(order.create_date, date_format)
            diff = a - b
            order.days = diff.days

    @api.model_cr
    def init(self):
        self.init_table()

    def init_table(self):
        """ Hybrid View """
        locations = self.env.context.get('locations')
        tools.drop_view_if_exists(self._cr, self._name.replace(".", "_"))
        select_query="""SELECT
           distinct ON (public.stock_production_lot.id)  public.stock_production_lot.id as lot_id  ,
           public.product_template.sku_code,
           public.product_template.name as product_name,
           public.product_template.id as product_id,
           stock_inventory_line.prod_lot_id,
           public.stock_production_lot.name as lot_name,
           public.stock_production_lot.product_uom_id,
           public.stock_production_lot.create_date as create_date,
           public.stock_warehouse.id as warehouse_id,
           public.stock_quant.location_id as location_id,
           NULL::Date as use_date,
           ROW_NUMBER () OVER (ORDER BY  stock_production_lot.id ) as id
           FROM
           public.product_product
           INNER JOIN
              public.product_template
              ON
              (public.product_product.product_tmpl_id = public.product_template.id)
           INNER JOIN
               public.stock_production_lot
               ON  
               (public.product_product.id = public.stock_production_lot.product_id)
           INNER JOIN
                public.stock_quant 
                ON
                (public.stock_quant.lot_id=public.stock_production_lot.id)   
           INNER JOIN
               public.stock_inventory_line
               ON
               (public.stock_production_lot.id = public.stock_inventory_line.prod_lot_id)
           INNER JOIN
               public.stock_location
               ON 
               (public.stock_inventory_line.location_id = public.stock_location.id)
           INNER JOIN
               public.stock_warehouse
               ON
                (public.stock_location.id = public.stock_warehouse.lot_stock_id)
        
        """
        if locations and not locations is None and len(locations)>0:
            location=str(tuple(locations))
            length=len(location)
            location=location[:length-2]
            location=location+")"
            select_query=select_query + " WHERE public.stock_quant.location_id in " + str(location)

        sql_query="CREATE VIEW aging_report AS ( " + select_query +")"
        self._cr.execute(sql_query)

    @api.model_cr
    def delete_and_create(self):
        self.init_table()

    # @api.multi
    # def _get_Data(self):
    #     for order in self:
    #          order.tracking = 'Lot#:' + str(order.name)
    #
    #          for p in order.quant_ids:
    #            order.qty = p.quantity
