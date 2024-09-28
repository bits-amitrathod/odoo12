# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools
import logging
import datetime
from datetime import date, datetime

logger = logging.getLogger(__name__)


class AgingReport(models.Model):
    _name = 'aging.report'
    _description = "Aging Report"
    _rec_name = 'product_id'

    # cr_date = fields.Date("Created date")
    qty = fields.Integer("Product Qty")

    sku_code = fields.Char(string="Product SKU", compute='get_quantity_byorm', store=False)
    prod_lot_id = fields.Many2one('stock.lot', 'stock  lot')
    product_name = fields.Char(string="Product Name")
    lot_name = fields.Char(string="Lot#")
    create_date = fields.Date(string="Last Updated Date")
    use_date = fields.Date(string="Expiry Date")
    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse')
    location_id = fields.Many2one('stock.location', string="Location")
    # tracking  = fields.Char("Tracking" ,compute='_get_Data',default=0)
    warehouse_name = fields.Char(string="Warehouse",compute='get_quantity_byorm', store=False)
    product_uom_id = fields.Char(string="UOM",compute='get_quantity_byorm', store=False)
    product_id = fields.Many2one('product.template', 'Product')
    type=fields.Char(string="Type")
    days = fields.Integer("Days", compute='get_quantity_byorm', store=False)
    avg_day = fields.Integer("AVG Days")

    #@api.multi
    def get_quantity_byorm(self):
        for order in self:
            order.sku_code=order.product_id.sku_code
            order.product_uom_id = order.product_id.uom_id.name
            order.warehouse_name = order.warehouse_id.name
            order.days = order.avg_day
                # if order.create_date :
                #     date_format = "%Y-%m-%d"
                #     today = date.today().strftime('%Y-%m-%d')
                #     a = datetime.strptime(str(today), date_format)
                #     b = datetime.strptime(str(order.create_date), date_format)
                #     diff = a - b
                #     order.days = diff.days

    #  @api.model_cr
    def init(self):
        self.init_table()

    def init_table(self):

        sql_query = """ 
                    TRUNCATE TABLE "aging_report"
                    RESTART IDENTITY;
                """
        self._cr.execute(sql_query)
        stock_location = self.env.context.get('stock_location')
        cust_location_id = self.env.context.get('cust_location_id')
        receiving_location = self.env.context.get('receiving_location')
        insert = "INSERT INTO aging_report" \
                 "(prod_lot_id,product_name,qty,lot_name, create_date,use_date,warehouse_id,location_id,product_id,type,avg_day)"
        # Stock Location
        select_query=insert + """ 
            SELECT
            public.stock_lot.id as prod_lot_id  ,
           public.product_template.name as product_name,
           sum(public.stock_quant.quantity) as qty ,
           public.stock_lot.name as lot_name,
           max(date(a.date)) as create_date,
           date(public.stock_lot.use_date) as use_date,
           public.stock_warehouse.id as warehouse_id,
           14 as location_id, 
           public.product_template.id as product_id,
           'Stock' as type,
           a.avg_day
           FROM public.product_product
           INNER JOIN
              public.product_template
              ON
              (public.product_product.product_tmpl_id = public.product_template.id)
           INNER JOIN
               public.stock_lot
               ON  
               (public.stock_lot.product_id=public.product_product.id )
           INNER JOIN
                public.stock_quant 
                ON
                (public.stock_quant.lot_id=public.stock_lot.id)   
           INNER JOIN
               public.stock_location
               ON 
               ( public.stock_location.id=public.stock_quant.location_id)
           INNER JOIN
               public.stock_warehouse
               ON
                (public.stock_location.id in (public.stock_warehouse.lot_stock_id,public.stock_warehouse.wh_output_stock_loc_id,wh_pack_stock_loc_id))
           INNER JOIN ( 
                select a.lot_id, max(a.date) as date,avg(DATE_PART('day',CURRENT_DATE :: TIMESTAMP - a.date :: TIMESTAMP )) as avg_day  from(        
                    SELECT stock_move_line.lot_id ,stock_move.date FROM public.stock_move 
                    INNER JOIN public.stock_move_line 
                    ON ( public.stock_move.id = public.stock_move_line.move_id and public.stock_move.state in ('done'))
                    where stock_move_line.lot_id is not null 
                    union
                    SELECT stock_move_line.lot_id , stock_move.date from stock_move_line
                    inner join stock_picking 
                    on stock_move_line.picking_id = stock_picking.id and stock_move_line.location_dest_id =14
                    inner join stock_move on stock_move.id = stock_move_line.move_id
                    where lot_id is not null
                ) a 
                group by a.lot_id
           ) as a
            ON stock_lot.id = a.lot_id  
            WHERE public.stock_quant.quantity>0
             
            group by  public.stock_lot.id ,public.product_template.name,public.stock_lot.name,public.stock_lot.create_date,
            public.stock_lot.use_date, public.stock_warehouse.id, public.product_template.id,a.avg_day
        
        """
        if stock_location and not stock_location is None :
            # select_query=select_query + " and public.stock_quant.location_id =%s "
            self._cr.execute(select_query)

        # Shipping
            select_query = insert + """ SELECT 
                            stock_move_line.lot_id as lot_id,
                            product_template.name as product_name,
                            sum(stock_move_line.reserved_uom_qty) as qty ,
                            stock_lot.name as lot_name ,
                            max(sale_order.date_order) as create_date,
                            stock_lot.use_date as use_date,
                            stock_warehouse.id as warehouse_id,
                            14 as location_id,
                            product_template.id as product_id,
                            'Shipping' as type,
                            avg(DATE_PART('day',CURRENT_DATE :: TIMESTAMP - sale_order.date_order :: TIMESTAMP )) as avg_day   
                    from sale_order
                    INNER JOIN stock_picking ON  stock_picking.sale_id = sale_order.id and sale_order.state in('sale') and stock_picking.picking_type_id =1 and stock_picking.state in('assigned','waiting')
                    LEFT JOIN stock_move_line ON stock_move_line.picking_id = stock_picking.id
                    LEFT JOIN stock_lot ON stock_lot.id = stock_move_line.lot_id
                    LEFT JOIN product_product ON product_product.id = stock_move_line.product_id
                    LEFT JOIN product_template ON product_template.id = product_product.product_tmpl_id
                    LEFT JOIN stock_warehouse ON stock_warehouse.wh_pack_stock_loc_id = stock_move_line.location_dest_id
                    WHERE product_template.id is not null and stock_move_line.lot_id is not null
                    group by stock_move_line.lot_id,product_template.name,stock_lot.name,stock_lot.use_date,stock_warehouse.id, product_template.id   
                                """
        if cust_location_id and not cust_location_id is None:
            # select_query = select_query + " and  public.stock_move.location_dest_id=%s "
            self._cr.execute(select_query, (cust_location_id,))



        # Receiving
        select_query = insert + """ SELECT 
                                public.stock_move_line.lot_id as prod_lot_id, 
                                public.product_template.name as product_name,
                                sum(public.stock_move_line.reserved_uom_qty) as qty, 
                                public.stock_lot.name as lot_name,
                                max(public.purchase_order.date_order) as create_date,
                                public.stock_lot.use_date as use_date,
                                1 as warehouse_id,
                                public.stock_move.location_id as location_id,
                                public.product_template.id as product_id,
                                'Receving' as type,
                                avg(DATE_PART('day',CURRENT_DATE :: TIMESTAMP - purchase_order.date_order :: TIMESTAMP )) as avg_day
                            FROM public.purchase_order 
                            INNER JOIN public.purchase_order_line ON (public.purchase_order.id = public.purchase_order_line.order_id and public.purchase_order.state in ('purchase')) 
                            INNER JOIN public.stock_move ON (public.purchase_order_line.id = public.stock_move.purchase_line_id) 
                            INNER JOIN public.stock_move_line ON (public.stock_move.id = public.stock_move_line.move_id) 
                            INNER JOIN public.stock_picking ON (public.stock_move_line.picking_id = public.stock_picking.id and public.stock_picking.state in ('assigned')) 
                            INNER JOIN public.product_product ON (public.purchase_order_line.product_id = public.product_product.id) 
                            INNER JOIN public.product_template ON (public.product_product.product_tmpl_id = public.product_template.id)
                            LEFT JOIN public.stock_lot ON (public.stock_move_line.lot_id = public.stock_lot.id)
                            LEFT JOIN public.stock_location ON (public.stock_location.id=public.stock_move.location_dest_id )
                            LEFT JOIN stock_warehouse ON (public.stock_warehouse.wh_pack_stock_loc_id = public.stock_location.location_id) 
                            group by public.stock_move_line.lot_id ,public.product_template.name,public.stock_lot.name, public.stock_lot.use_date,
                            stock_warehouse.id,public.stock_move.location_id,public.product_template.id      
                   """
        if receiving_location and not receiving_location is None:
            # select_query = select_query + " and  public.stock_move.location_dest_id=%s"
            self._cr.execute(select_query, (receiving_location,))

    #  @api.model_cr
    def delete_and_create(self):
        self.init_table()

    # #@api.multi
    # def _get_Data(self):
    #     for order in self:
    #          order.tracking = 'Lot#:' + str(order.name)
    #
    #          for p in order.quant_ids:
    #            order.qty = p.quantity
