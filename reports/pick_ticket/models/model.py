from odoo import api, fields, models, tools
import odoo.addons.decimal_precision as dp

class PickTicketReport(models.Model):
    _name = "report.pick.ticket"
    _description = "PickTicketReport"
    # _auto = False

    _inherits = {'stock.picking': 'picking_id'}

    carrier_info = fields.Char(string="Sale Order#")
    move_id = fields.Many2one('stock.move', string="Customer Name")
    qty_done = fields.Float(string="Quantity",digits='Product Unit of Measure')
    location_id = fields.Many2one('stock.location', string="Location")
    location_dest_id = fields.Many2one('stock.location', string='Destionation', )
    state = fields.Char(string='state', )
    sale_id = fields.Many2one('sale.order', string="Sale Order Id")
    partner_id = fields.Many2one('res.partner', string="Partner Id")
    carrier_id = fields.Many2one('delivery.carrier', string="Carrier Id")
    product_id = fields.Many2one('product.product', string="Carrier Id")
    picking_id = fields.Many2one('stock.picking', string='Pick Number', required=True, ondelete='cascade')
    product_uom_id = fields.Many2one('uom.uom', 'UOM ')
    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse')
    scheduled_date = fields.Datetime(string='Scheduled Date')
    picking_type = fields.Char(string='Type', )

    def init(self):
        # self.init_table()
        pass

    def init_table(self):
        tools.drop_view_if_exists(self._cr, self._name.replace(".", "_"))

        select_query = """ 
            SELECT
                CASE
                    WHEN res_partner.carrier_info IS NOT NULL
                    THEN res_partner.carrier_info
                    ELSE delivery_carrier.name
                END AS carrier_info,
                stock_move_line.move_id,
                stock_move_line.qty_done,
                stock_move_line.location_id,
                stock_move_line.location_dest_id,
                stock_move_line.state,
                sale_order.id      AS sale_id,
                stock_move_line.id AS id,
                sale_order.partner_id,
                sale_order.carrier_id,
                stock_move_line.product_id,
                stock_move_line.picking_id,
                stock_move_line.product_uom_id,
                sale_order.warehouse_id,
                stock_picking.scheduled_date,
                stock_picking_type.name as picking_type
            FROM
                stock_move_line
            INNER JOIN
                stock_picking
            ON
                (
                    stock_move_line.picking_id = stock_picking.id)
            INNER JOIN
                sale_order
            ON
                (
                    stock_picking.sale_id = sale_order.id)
            INNER JOIN
                res_partner
            ON
                (
                    sale_order.partner_id = res_partner.id)
            LEFT OUTER JOIN
                delivery_carrier
            ON
                (
                    sale_order.carrier_id = delivery_carrier.id)
            INNER JOIN
                product_product
            ON
                (
                    stock_move_line.product_id = product_product.id)
            INNER JOIN
                stock_picking_type
            ON
                (
                    stock_picking.picking_type_id = stock_picking_type.id)
                            """

        where_clause = "  WHERE  stock_picking.scheduled_date IS NOT NULL "

        sql_query = "CREATE VIEW " + self._name.replace(".", "_") + " AS ( " + select_query + where_clause + " )"
        self._cr.execute(sql_query)

    def delete_and_create(self):
        self.init_table()