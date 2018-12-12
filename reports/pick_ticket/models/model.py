from odoo import api, fields, models, tools
import logging
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class ReportPickTicketGroupByOrderDate(models.TransientModel):
    _name = 'report.pick.ticket.groupby.order'
    _description = 'Pick Ticket Group By Order'

    compute_at_date = fields.Selection([
        (0, 'Order'),
        (1, 'Date Range ')
    ], string="Compute", help="Choose to analyze the Show Summary or from a specific date in the past.")

    start_date = fields.Date('Start Date', default=fields.Datetime.now, required=True)

    end_date = fields.Date('End Date', default=fields.Datetime.now, required=True)

    order_number = fields.Many2many('sale.order', string="Sale Order")

    def open_table(self):

        context = {}
        if self.compute_at_date:
            s_date = self.string_to_date(str(self.start_date))
            e_date = self.string_to_date(str(self.end_date))
            context.update({'s_date': s_date, 'e_date': e_date})
        else:
            context.update({'sale_number': self.order_number})

        tree_view_id = self.env.ref('pick_ticket.pick_report_list_view').id

        res_model = 'report.order.pick.ticket'
        self.env[res_model].with_context(context).delete_and_create()

        action = {
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id, 'tree')],
            'view_mode': 'tree',
            'name': 'Pick Ticket',
            'res_model': res_model,
            'context': {'group_by': 'sale_id'},
        }

        if self.compute_at_date:
            return action
        else:
            return action

    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(date_string, DEFAULT_SERVER_DATE_FORMAT).date()


class PickTicketReport(models.Model):
    _name = "report.order.pick.ticket"
    _auto = False

    carrier_info = fields.Char(string="Sale Order")
    move_id = fields.Many2one('stock.move', string="Customer Name")
    qty_done = fields.Char(string="Quantity")
    location_id = fields.Many2one('stock.location', string="Location")
    location_dest_id = fields.Many2one('stock.location', string='Destionation', )
    state = fields.Char(string='state', )
    sale_id = fields.Many2one('sale.order', string="Sale Order Id")
    partner_id = fields.Many2one('res.partner', string="Partner Id")
    carrier_id = fields.Many2one('delivery.carrier', string="Carrier Id")
    product_id = fields.Many2one('product.product', string="Carrier Id")

    @api.model_cr
    def init(self):
        self.init_table()

    def init_table(self):
        s_date = self.env.context.get('s_date')
        e_date = self.env.context.get('e_date')
        sale_number = self.env.context.get('sale_number')
        tools.drop_view_if_exists(self._cr, self._name.replace(".", "_"))

        select_query = """ SELECT
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
                   sale_order.id as sale_id ,
                   stock_move_line.id as id,
                   sale_order.partner_id,
                   sale_order.carrier_id,
                   stock_move_line.product_id
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
                        stock_move_line.product_id = product_product.id)"""

        where_clause = "  WHERE  stock_picking.scheduled_date IS NOT NULL "
        AND = " AND "

        if not s_date is None:
            select_query = select_query + where_clause + AND + " stock_picking.scheduled_date >= '" + \
                           str(s_date) + "'"

        if not e_date is None:
            select_query = select_query + AND + " stock_picking.scheduled_date <= '" + str(e_date) + "'"

        if hasattr(sale_number, 'ids') and len(sale_number.ids):
            select_query = select_query + AND + " sale_order.id in (" + ", ".join(str(x) for x in sale_number.ids) + ")"

        sql_query = "CREATE VIEW " + self._name.replace(".", "_") + " AS ( " + select_query + " )"
        self._cr.execute(sql_query)

    @api.model_cr
    def delete_and_create(self):
        self.init_table()
