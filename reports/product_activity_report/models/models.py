from odoo import models, fields
import logging
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

_logger = logging.getLogger(__name__)


class ReportPickTicketGroupByOrderDate(models.TransientModel):
    _name = 'product.activity.report.popup'
    _description = 'Pick Ticket Group By Order'

    start_date = fields.Date('Start Date', default=datetime.date.today() + datetime.timedelta(-30), required=True)
    end_date = fields.Date('End Date', default=fields.date.today(), required=True)
    sku = fields.Many2one('product.product', string='Product SKU',
                          domain="[('active','=',True),('product_tmpl_id.type','=','product')]")
    location_id = fields.Selection([
        ('Purchase', 'Purchase'),
        ('Sales', 'Sales'),
        ('Receive', 'Receive'),
        ('Stock', 'Stock'),
        ('Scrap', 'Scrap')
    ], string="Location", default=0, help="Choose to analyze the Show Summary or from a specific location.")

    def open_table(self):
        #  margins_context = {'start_date': self.string_to_date(str(self.start_date)),
        #                    'end_date': self.string_to_date(str(self.end_date))}

        tree_view_id = self.env.ref('product_activity_report.product_activity_report_list').id
        form_view_id = self.env.ref('product_activity_report.product_activity_report_form').id
        res_model = 'product.activity.report'
        self.env[res_model].delete_and_create()  # with_context(margins_context).

        action = {
            "type": "ir.actions.act_window",
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            "res_model": res_model,
            "name": "Product Activity Report",
            "context": {"search_default_product_activity": 1},
            'domain': []
        }
        if self.start_date:
            action["domain"].append(('date', '>=', self.start_date))

        if self.end_date:
            action["domain"].append(('date', '<=', self.end_date))

        if self.sku:
            action["domain"].append(('product_id.id', '=', self.sku.id))

        if self.location_id:
            action["domain"].append(('type', '=', self.location_id))

        return action

    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(date_string, DEFAULT_SERVER_DATE_FORMAT).date()


class ReportProductActivity(models.Model):
    _name = "product.activity.report"
    _description = "report product activity report"

    warehouse = fields.Char(string="Warehouse")
    date = fields.Date(string="Date")
    location_id = fields.Integer(string="location_id")
    location = fields.Char(string="Location")
    event = fields.Char(string="Event")
    change_qty = fields.Integer(string="Change Qty")
    agent = fields.Char(string="User")
    sku = fields.Char(string="Product SKU")
    lot = fields.Char(string="Lot")
    expiration_date = fields.Date(string="Expiration Date")
    type = fields.Char(string="Type")
    product_id = fields.Many2one('product.template', 'Product')

    def init(self):
        self.init_table()

    def init_table(self):
        sql_query = """ 
            TRUNCATE TABLE "product_activity_report"
            RESTART IDENTITY;
        """
        self._cr.execute(sql_query)
        # start_date = self.env.context.get('start_date')
        # end_date = self.env.context.get('end_date')
        #
        # if not start_date is None and not end_date is None:
        #     date_clause = " BETWEEN '" + str(start_date) + "' AND '" + str(end_date) + "' "
        # else:
        #     date_clause = False

        insert = "INSERT INTO product_activity_report" \
                 "(warehouse, date,location_id, location,event,change_qty,agent,sku,lot,expiration_date,product_id,type)"

        # -------------------- purchase ------------------------
        sql_query = insert + """ 
                    SELECT
                        stock_warehouse.name AS warehouse,
                        stock_picking.scheduled_date as date,
                        stock_location.id as location_id,
                        stock_warehouse.code || '/' || stock_location.name AS location,
                        purchase_order.name                                       AS event,
                        purchase_order_line.product_qty                           AS change_qty,
                        res_partner.name                                          AS user,
                        product_template.sku_code                                 AS sku,
                        stock_lot.name                                            AS lot,
                        stock_lot.use_date                                        AS expiration_date,
                        product_template.id                                   AS product_id,
                        'Purchase' as type 
                    FROM
                        purchase_order_line
                    INNER JOIN
                        purchase_order
                    ON
                        (
                            purchase_order_line.order_id = purchase_order.id)
                    INNER JOIN
                        product_product
                    ON
                        (
                            purchase_order_line.product_id = product_product.id)
                    INNER JOIN
                        product_template
                    ON
                        (
                            product_product.product_tmpl_id = product_template.id)
                    INNER JOIN
                        res_users
                    ON
                        (
                            product_template.id = res_users.id)
                    INNER JOIN
                        res_partner
                    ON
                        (
                            res_users.partner_id = res_partner.id)
                    INNER JOIN
                        stock_move
                    ON
                        (
                            purchase_order_line.id = stock_move.purchase_line_id)
                    INNER JOIN
                        stock_move_line
                    ON
                        (
                            stock_move.id = stock_move_line.move_id)
                    LEFT OUTER JOIN
                        stock_lot
                    ON
                        (
                            stock_move_line.lot_id = stock_lot.id)
                    INNER JOIN
                        stock_picking
                    ON
                        (
                            stock_move_line.picking_id = stock_picking.id)
                    INNER JOIN
                        stock_location
                    ON
                        (
                            stock_picking.location_dest_id = stock_location.id)
                    INNER JOIN
                        stock_warehouse
                    ON
                        (
                            stock_location.id = stock_warehouse.lot_stock_id)
                    WHERE stock_picking.state = 'done'
                """
        # if not date_clause is False:
        #     sql_query = sql_query + " AND  stock_picking.scheduled_date" + date_clause

        self._cr.execute(sql_query)

        # -------------------- Sales ------------------------
        dist_location = self.env['stock.location'].search(
            [('name', '=', 'Customers')]).ids
        sql_query = insert + """
                    SELECT
                        stock_warehouse.name                                      AS warehouse,
                        stock_picking.scheduled_date                                     AS DATE,
                        stock_location.id as location_id,
                        stock_warehouse.code || '/' || 'Customers' AS location,
                        sale_order.name                                           AS event,
                        (stock_move_line.qty_done*-1)                                  AS change_qty,
                        res_partner.name                                          AS USER,
                        product_template.sku_code                                 AS sku,
                        stock_lot.name                                 AS lot,
                        stock_lot.use_date                         AS expiration_date,
                        product_template.id                                   AS product_id,
                        'Sales' as type
                    FROM
                        sale_order
                    INNER JOIN
                        stock_warehouse
                    ON
                        (
                            sale_order.warehouse_id = stock_warehouse.id)
                    INNER JOIN
                        sale_order_line
                    ON
                        (
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
                            product_product.product_tmpl_id = product_template.id)
                    INNER JOIN
                        stock_move
                    ON
                        (
                            sale_order_line.id = stock_move.sale_line_id)
                    INNER JOIN
                        stock_move_line
                    ON
                        (
                            stock_move.id = stock_move_line.move_id)
                    INNER JOIN
                        stock_lot
                    ON
                        (
                            stock_move_line.lot_id = stock_lot.id)
                    INNER JOIN
                        stock_picking
                    ON
                        (
                            stock_move_line.picking_id = stock_picking.id)
                    INNER JOIN
                        stock_location
                    ON
                        (
                            stock_picking.location_id = stock_location.id)
                    LEFT OUTER JOIN
                        res_users
                    ON
                        (
                            sale_order.user_id = res_users.id)
                    INNER JOIN
                        res_partner
                    ON
                        (
                            res_users.partner_id = res_partner.id)

                    WHERE stock_picking.state = 'done' and stock_picking.location_dest_id = ANY (ARRAY[%s])
                        """

        # if not date_clause is False:
        #     sql_query = sql_query+ " AND stock_picking.scheduled_date" + date_clause

        self._cr.execute(sql_query, (dist_location,))

        # -------------------- Stock ------------------------
        sql_query = insert + """
                    SELECT
                        stock_warehouse.name                                      AS warehouse,
                        stock_quant.in_date,
                        stock_location.id as location_id,
                        stock_warehouse.code || '/' || stock_location.name AS location,
                        product_template.name                                      AS event,
                        stock_quant.quantity                                 AS change_qty,
                        res_partner.name                                          AS USER,
                        product_template.sku_code                                 AS sku,
                        stock_lot.name                                            AS lot,
                        stock_lot.use_date                                        AS expiration_date,
                        product_template.id                                   AS product_id,
                        'Stock' as type
                    FROM
                        stock_quant
                    INNER JOIN
                        stock_location
                    ON
                        (
                            stock_quant.location_id = stock_location.id)
                    INNER JOIN
                        stock_warehouse
                    ON
                        (
                            stock_location.id  =  stock_warehouse.lot_stock_id)
                    INNER JOIN
                        res_users
                    ON
                        (
                            stock_quant.write_uid = res_users.id)
                    INNER JOIN
                        res_partner
                    ON
                        (
                            res_users.partner_id = res_partner.id)
                    INNER JOIN
                        product_product
                    ON
                        (
                            stock_quant.product_id = product_product.id)
                    INNER JOIN
                        product_template
                    ON
                        (
                            product_product.product_tmpl_id = product_template.id)
                    INNER JOIN
                        stock_lot
                    ON
                        (
                            stock_quant.lot_id = stock_lot.id)
                    WHERE stock_quant.quantity > 0
                        """
        # if not date_clause is False:
        #     sql_query = sql_query+ " and stock_inventory.date" + date_clause

        self._cr.execute(sql_query)

        # -------------------- Srcap ------------------------
        sql_query = insert + """
                    SELECT
                        stock_warehouse.name                                      AS warehouse,
                        stock_scrap.date_done                                 AS DATE,
                        stock_location.id as location_id,
                        stock_warehouse.code || '/' || stock_location.name AS location,
                        stock_scrap.name                                          AS event,
                        (stock_scrap.scrap_qty*-1)                                     AS change_qty,
                        res_partner.name                                          AS USER,
                        product_template.sku_code                                 AS sku,
                        stock_lot.name                                 AS lot,
                        stock_lot.use_date                         AS expiration_date,
                        product_template.id                                   AS product_id,
                        'Scrap' as type
                    FROM
                        product_product
                    INNER JOIN
                        product_template
                    ON
                        (
                            product_product.product_tmpl_id = product_template.id)
                    INNER JOIN
                        stock_scrap
                    ON
                        (
                            product_product.id = stock_scrap.product_id)
                    INNER JOIN
                        stock_location
                    ON
                        (
                            stock_scrap.location_id = stock_location.id)
                    INNER JOIN
                        stock_warehouse
                    ON
                        (
                            stock_location.id = stock_warehouse.lot_stock_id)
                    INNER JOIN
                        res_users
                    ON
                        (
                            stock_scrap.write_uid = res_users.id)
                    INNER JOIN
                        res_partner
                    ON
                        (
                            res_users.partner_id = res_partner.id)
                    INNER JOIN
                        stock_lot
                    ON
                        (
                            stock_scrap.lot_id = stock_lot.id) 
                    WHERE stock_scrap.state = 'done'
                                """

        # if not date_clause is False:
        #     sql_query = sql_query+" AND stock_scrap.date_expected" + date_clause

        self._cr.execute(sql_query)

        # -------------------- Receive ------------------------

        dist_location = self.env['stock.location'].search(
            [('name', '=', 'Stock')]).ids
        if dist_location:
            sql_query = insert + """
                               SELECT            
                                   stock_warehouse.name                                      AS warehouse,
                                   stock_picking.scheduled_date                                     AS DATE,
                                   stock_location.id as location_id,
                                   stock_warehouse.code || '/' || stock_location.name AS location,
                                   sale_order.name                                           AS event,
                                   (stock_move_line.qty_done)                                  AS change_qty,
                                   res_partner.name                                          AS USER,
                                   product_template.sku_code                                 AS sku,
                                   stock_lot.name                                 AS lot,
                                   stock_lot.use_date                         AS expiration_date,
                                   product_template.id                                   AS product_id,
                                   'Receive' as type
                               FROM
                                   stock_picking
                               INNER JOIN sale_order

                               ON  (sale_order.id= stock_picking.sale_id)  

                               INNER JOIN
                                   stock_warehouse
                               ON
                                   (
                                       sale_order.warehouse_id = stock_warehouse.id)

                               INNER JOIN
                                   stock_move_line
                               ON
                                   (
                                       stock_move_line.picking_id = stock_picking.id)

                               INNER JOIN
                                   product_product
                               ON
                                   (
                                       product_product.id = stock_move_line.product_id)
                               INNER JOIN
                                   product_template
                               ON
                                   (
                                       product_template.id=product_product.product_tmpl_id)        
                               INNER JOIN
                                   stock_lot
                               ON
                                   (
                                       stock_lot.id=stock_move_line.lot_id  )
                               
                               INNER JOIN
                                   stock_location
                               ON
                                   (
                                       stock_location.id=stock_picking.location_dest_id )
                                INNER JOIN
                                   res_users
                               ON
                                   (
                                       sale_order.user_id = res_users.id)
                               INNER JOIN
                                   res_partner
                               ON
                                   (
                                       res_users.partner_id = res_partner.id)

                               WHERE stock_picking.state = 'done' and  stock_picking.location_dest_id = ANY (ARRAY[%s])
                                   """

            # if not date_clause is False:
            #     sql_query = sql_query+ " AND stock_picking.scheduled_date" + date_clause

            self._cr.execute(sql_query,(dist_location,))

    def delete_and_create(self):
        self.init_table()

        # return {
        #     "type": "ir.actions.act_window",
        #     "view_mode": "tree",
        #     "res_model": self._name,
        #     "name": "Product Activity Report",
        #     "context": {"search_default_product_activity": 1}
        # }
