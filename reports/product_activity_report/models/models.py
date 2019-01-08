from odoo import models, fields
import logging
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

_logger = logging.getLogger(__name__)


class ReportPickTicketGroupByOrderDate(models.TransientModel):
    _name = 'product.activity.report.popup'
    _description = 'Pick Ticket Group By Order'

    start_date = fields.Date('Start Date', default=datetime.datetime.now() + datetime.timedelta(-30), required=True)
    end_date = fields.Date('End Date', default=fields.Datetime.now, required=True)
    sku = fields.Char(string="Product SKU")
    location_id = fields.Many2one('stock.location', string="Location", domain="[('usage', '=', 'internal')]")



    def open_table(self):
      #  margins_context = {'start_date': self.string_to_date(str(self.start_date)),
       #                    'end_date': self.string_to_date(str(self.end_date))}

        tree_view_id = self.env.ref('product_activity_report.product_activity_report_list').id
        res_model = 'product.activity.report'
        self.env[res_model].delete_and_create() #with_context(margins_context).

        action = {
            "type": "ir.actions.act_window",
            'views': [(tree_view_id, 'tree')],
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
                action["domain"].append(('sku', 'ilike', self.sku))

        if self.location_id.id :
                action["domain"].append(('location_id', '=', self.location_id.id))

        return action

    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(date_string, DEFAULT_SERVER_DATE_FORMAT).date()


class ReportProductActivity(models.TransientModel):
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
                 "(warehouse, date,location_id, location,event,change_qty,agent,sku,lot,expiration_date,type)"

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
                        stock_production_lot.name                                 AS lot,
                        stock_production_lot.removal_date                         AS expiration_date,
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
                            product_template.responsible_id = res_users.id)
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
                        stock_production_lot
                    ON
                        (
                            stock_move_line.lot_id = stock_production_lot.id)
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
        sql_query = insert + """
                    SELECT
                        stock_warehouse.name                                      AS warehouse,
                        stock_picking.scheduled_date                                     AS DATE,
                        stock_location.id as location_id,
                        stock_warehouse.code || '/' || stock_location.name AS location,
                        sale_order.name                                           AS event,
                        (stock_move_line.qty_done*-1)                                  AS change_qty,
                        res_partner.name                                          AS USER,
                        product_template.sku_code                                 AS sku,
                        stock_production_lot.name                                 AS lot,
                        stock_production_lot.removal_date                         AS expiration_date,
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
                        stock_production_lot
                    ON
                        (
                            stock_move_line.lot_id = stock_production_lot.id)
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
                    
                    WHERE stock_picking.state = 'done'
                        """

        # if not date_clause is False:
        #     sql_query = sql_query+ " AND stock_picking.scheduled_date" + date_clause

        self._cr.execute(sql_query)

        # -------------------- Stock ------------------------
        sql_query = insert + """
                    SELECT
                        stock_warehouse.name                                      AS warehouse,
                        stock_inventory.date,
                        stock_location.id as location_id,
                        stock_warehouse.code || '/' || stock_location.name AS location,
                        stock_inventory.name                                      AS event,
                        stock_inventory_line.product_qty                          AS change_qty,
                        res_partner.name                                          AS USER,
                        product_template.sku_code                                 AS sku,
                        stock_production_lot.name                                 AS lot,
                        stock_production_lot.removal_date                         AS expiration_date,
                        'Stock' as type
                    FROM
                        stock_inventory_line
                    INNER JOIN
                        stock_location
                    ON
                        (
                            stock_inventory_line.location_id = stock_location.id)
                    INNER JOIN
                        stock_warehouse
                    ON
                        (
                            stock_location.id = stock_warehouse.lot_stock_id)
                    INNER JOIN
                        stock_inventory
                    ON
                        (
                            stock_inventory_line.inventory_id = stock_inventory.id)
                    INNER JOIN
                        res_users
                    ON
                        (
                            stock_inventory_line.write_uid = res_users.id)
                    INNER JOIN
                        res_partner
                    ON
                        (
                            res_users.partner_id = res_partner.id)
                    INNER JOIN
                        product_product
                    ON
                        (
                            stock_inventory_line.product_id = product_product.id)
                    INNER JOIN
                        product_template
                    ON
                        (
                            product_product.product_tmpl_id = product_template.id)
                    INNER JOIN
                        stock_production_lot
                    ON
                        (
                            stock_inventory_line.prod_lot_id = stock_production_lot.id)
                    WHERE stock_inventory.state = 'done'
                        """
        # if not date_clause is False:
        #     sql_query = sql_query+ " and stock_inventory.date" + date_clause

        self._cr.execute(sql_query)

        # -------------------- Srcap ------------------------
        sql_query = insert + """
                    SELECT
                        stock_warehouse.name                                      AS warehouse,
                        stock_scrap.date_expected                                 AS DATE,
                        stock_location.id as location_id,
                        stock_warehouse.code || '/' || stock_location.name AS location,
                        stock_scrap.name                                          AS event,
                        (stock_scrap.scrap_qty*-1)                                     AS change_qty,
                        res_partner.name                                          AS USER,
                        product_template.sku_code                                 AS sku,
                        stock_production_lot.name                                 AS lot,
                        stock_production_lot.removal_date                         AS expiration_date,
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
                        stock_production_lot
                    ON
                        (
                            stock_scrap.lot_id = stock_production_lot.id) 
                    WHERE stock_scrap.state = 'done'
                                """

        # if not date_clause is False:
        #     sql_query = sql_query+" AND stock_scrap.date_expected" + date_clause

        self._cr.execute(sql_query)

    def delete_and_create(self):
        self.init_table()

        # return {
        #     "type": "ir.actions.act_window",
        #     "view_mode": "tree",
        #     "res_model": self._name,
        #     "name": "Product Activity Report",
        #     "context": {"search_default_product_activity": 1}
        # }
