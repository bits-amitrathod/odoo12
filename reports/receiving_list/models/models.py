# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, tools
import odoo.addons.decimal_precision as dp
import logging
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc

_logger = logging.getLogger(__name__)


class ReceivingListPopUp(models.TransientModel):
    _name = 'popup.receiving.list'

    order_type = fields.Selection([
        ('1', 'PO'),
        ('0', 'SO'),
    ], string="Order Type", default='1', help="Choose to analyze the Show Summary or from a specific date in the past.",
        required=True)

    sale_order_id = fields.Many2one('sale.order', string='Order Number'
    # , domain = "[('picking_ids.state','in',('assigned','done')),('picking_ids.picking_type_id','=',2)]"
                                    )

    purchase_order_id = fields.Many2one('purchase.order', string='Order Number',
                                        domain="[('picking_ids.state','in',('assigned','done')),('picking_type_id.code','=','incoming')]",
                                        order='picking_name')

    def open_table(self):
        data = {'order_type': self.order_type}
        if self.order_type == '1':
            self.env['report.receiving.list.po'].delete_and_create()
            data['order_id'] = self.purchase_order_id.id
        else:
            self.env['report.receiving.list.so'].delete_and_create()
            data['order_id'] = self.sale_order_id.id

        action = self.env.ref('receiving_list.action_report_receiving_list').report_action([], data=data)
        action.update({'target': 'main'})

        return action


class ReceivingListPoReport(models.Model):
    _name = "report.receiving.list.po"
    _auto = False

    order_id = fields.Many2one('purchase.order', string='Purchase Order#', )
    partner_id = fields.Many2one('res.partner', string="Partner Id")
    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse')
    picking_type_id = fields.Many2one('stock.picking.type', "Operation Type")
    location_dest_id = fields.Many2one('stock.location', string='Destionation', )
    picking_name = fields.Char('Picking #')
    product_tmpl_id = fields.Many2one('product.template', "Product")
    product_uom_qty = fields.Float('Quantity', digits=dp.get_precision('Product Unit of Measure'))
    qty_done = fields.Float('Qty Received', digits=dp.get_precision('Product Unit of Measure'))
    date_done = fields.Datetime('Date Done')
    product_uom_id = fields.Many2one('uom.uom', 'UOM')
    state = fields.Selection([
        ('draft', 'New'), ('cancel', 'Cancelled'),
        ('waiting', 'Waiting Another Move'),
        ('confirmed', 'Waiting Availability'),
        ('partially_available', 'Partially Available'),
        ('assigned', 'Available'),
        ('done', 'Done')], string='Status')

    def init(self):
        self.init_table()

    def init_table(self):
        tools.drop_view_if_exists(self._cr, self._name.replace(".", "_"))
        # purchase = self.env['purchase.order'].search(
        #     [('id', '=', 7499)])
        # _logger.info("id :%r", purchase)
        select_query = """
                SELECT
                    ROW_NUMBER () OVER (ORDER BY stock_move_line.id) as id, 
                    purchase_order_line.order_id,
                    purchase_order.partner_id,
                    stock_warehouse.id as warehouse_id,
                    stock_picking.state,
                    stock_picking.picking_type_id,
                    stock_picking.date_done,
                    stock_picking.name as picking_name,
                    product_product.product_tmpl_id,
                    stock_picking.location_dest_id,
                    stock_move_line.reserved_qty,
                    stock_move_line.qty_done,
                    stock_move_line.product_uom_id
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
                    stock_move
                ON
                    (
                        purchase_order_line.id = stock_move.purchase_line_id)
                INNER JOIN
                    stock_move_line
                ON
                    (
                        stock_move.id = stock_move_line.move_id)
                INNER JOIN
                    stock_picking
                ON
                    (
                        stock_move_line.picking_id = stock_picking.id)
                INNER JOIN
                    stock_picking_type
                ON
                    (
                        stock_picking.picking_type_id = stock_picking_type.id)
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
                INNER JOIN
                    product_template
                ON
                    (
                        product_product.product_tmpl_id = product_template.id)
                WHERE
                    stock_picking_type.code = 'incoming'
                AND stock_picking.state in ('assigned','done')
        """

        sql_query = "CREATE VIEW " + self._name.replace(".", "_") + " AS ( " + select_query + " )"
        self._cr.execute(sql_query)

    def delete_and_create(self):
        self.init_table()


class ReceivingListReport(models.Model):
    _name = "report.receiving.list.so"
    _auto = False

    order_id = fields.Many2one('sale.order', string='Sale Order#', )
    partner_id = fields.Many2one('res.partner', string="Partner Id")
    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse')
    picking_type_id = fields.Many2one('stock.picking.type', "Operation Type")
    location_dest_id = fields.Many2one('stock.location', string='Destionation', )
    picking_name = fields.Char('Picking #')
    product_tmpl_id = fields.Many2one('product.template', "Product")
    product_uom_qty = fields.Float('Quantity', digits=dp.get_precision('Product Unit of Measure'))
    qty_done = fields.Float('Qty Received', digits=dp.get_precision('Product Unit of Measure'))
    date_done = fields.Datetime('Date Done')
    product_uom_id = fields.Many2one('uom.uom', 'UOM')
    state = fields.Selection([
        ('draft', 'New'), ('cancel', 'Cancelled'),
        ('waiting', 'Waiting Another Move'),
        ('confirmed', 'Waiting Availability'),
        ('partially_available', 'Partially Available'),
        ('assigned', 'Available'),
        ('done', 'Done')], string='Status')

    def init(self):
        self.init_table()

    def init_table(self):
        tools.drop_view_if_exists(self._cr, self._name.replace(".", "_"))

        select_query = """
                SELECT
                    ROW_NUMBER () OVER (ORDER BY stock_move_line.id) as id, 
                    stock_picking.sale_id as order_id,
                    sale_order.partner_id,
                    sale_order.warehouse_id,
                    stock_picking.state,
                    stock_picking.picking_type_id,
                    stock_picking.name as picking_name,
                    stock_picking.date_done,
                    product_product.product_tmpl_id,
                    stock_picking.location_dest_id,
                    stock_move_line.reserved_qty,
                    stock_move_line.qty_done,
                    stock_move_line.product_uom_id
                FROM
                    stock_picking
                INNER JOIN
                    stock_move_line
                ON
                    (
                        stock_move_line.picking_id = stock_picking.id)

                INNER JOIN
                    stock_picking_type
                ON
                    (
                        stock_picking.picking_type_id = stock_picking_type.id)

                INNER JOIN
                    product_product
                ON
                    (
                        stock_move_line.product_id = product_product.id)
                INNER JOIN
                    product_template
                ON
                    (
                        product_product.product_tmpl_id = product_template.id)
                INNER JOIN
                    sale_order
                ON
                    (
                        stock_picking.sale_id = sale_order.id)
                WHERE
                    stock_picking.state in ('assigned','done') and stock_picking.location_id in (12,16,9)
        """

        sql_query = "CREATE VIEW " + self._name.replace(".", "_") + " AS ( " + select_query + " )"
        self._cr.execute(sql_query)

    def delete_and_create(self):
        self.init_table()