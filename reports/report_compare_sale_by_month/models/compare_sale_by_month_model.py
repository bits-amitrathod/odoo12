
from odoo import api, fields, models
import datetime

class comparebymonth():
    product_name = ''
    current_month_total_qty = 0
    current_month_total_amount = 0
    last_month_total_qty = 0
    last_month_total_amount = 0
    sku=''


class CompareSaleByMonth(models.Model):
    _inherit = "product.product"

    # sku_name = fields.Char("Product ",store=False)
    product_name = fields.Char("Product Name ",store=False)
    last_month_total_qty = fields.Float("Last Month Total Qty", compute = '_compare_data', store=False)
    last_month_total_amount = fields.Monetary("Last Month Total Amount", store=False)
    current_month_total_qty = fields.Float("Current Month Total Qty", store=False)
    current_month_total_amount = fields.Monetary("Current Month Total Amount", store=False)
    # location = fields.Char(string='Location')

    def _compare_data(self):
        sale_orders = self.env['sale.order'].search([('state','in',('sale','done'))])
        if self.env.context.get('current_start_date'):
            s_date = (fields.Datetime.from_string(self.env.context.get('current_start_date')).date())
            l_date = (fields.Datetime.from_string(self.env.context.get('current_end_date')).date())
            ps_date =(fields.Datetime.from_string(self.env.context.get('last_start_date')).date())
            pl_date = (fields.Datetime.from_string(self.env.context.get('last_end_date')).date())
        else :
            s_date = (fields.date.today() - datetime.timedelta(days=30))
            l_date = (fields.date.today())
            ps_date = (fields.date.today() - datetime.timedelta(days=60))
            pl_date = (fields.date.today() - datetime.timedelta(days=31))

        filtered_by_current_month = list(filter(
            lambda x: fields.Datetime.from_string(x.date_order).date() >= s_date and fields.Datetime.from_string(
                x.date_order).date() <= l_date, sale_orders))

        filtered_by_last_month = list(filter(
            lambda x: fields.Datetime.from_string(x.date_order).date() >= ps_date and fields.Datetime.from_string(
                x.date_order).date() <= pl_date, sale_orders))
        dat = self.addObject(filtered_by_current_month, filtered_by_last_month)

        for order in self:
            if order.id in dat:
                if int(dat[order.id].current_month_total_qty) > 0 or int(dat[order.id].last_month_total_qty) > 0:
                    # order.sku_name = dat[order.id].sku
                    order.product_name = dat[order.id].product_name
                    order.last_month_total_qty = dat[order.id].last_month_total_qty
                    order.last_month_total_amount = dat[order.id].last_month_total_amount
                    order.current_month_total_qty = dat[order.id].current_month_total_qty
                    order.current_month_total_amount = dat[order.id].current_month_total_amount
                    # order.location = dat[order.id].location

    @api.multi
    def addObject(self, filtered_by_current_month, filtered_by_last_month):
        product_dict = {}
        for record in filtered_by_current_month:
            stock_picking = self.env['stock.picking'].search([('sale_id', '=', record.id)])
            if len(stock_picking) == 1:
                for r1 in record.order_line:
                    stock_move = self.env['stock.move'].search([('picking_id', '=', stock_picking.id), ('product_id', '=', r1.product_id.id),('state', 'in', ('done', 'partially_available'))])
                    if len(stock_move) == 1:
                        stock_move_line = self.env['stock.move.line'].search([('move_id', '=', stock_move.id), ('state', 'in', ('done', 'partially_available'))])
                        if len(stock_move_line) == 1:
                            if int(stock_move_line.qty_done) > 0:
                                if r1.product_id.id in product_dict:
                                    data = product_dict[r1.product_id.id]
                                    data.current_month_total_qty = data.current_month_total_qty + stock_move_line.qty_done
                                    data.current_month_total_amount = data.current_month_total_amount + (r1.price_unit * stock_move_line.qty_done)
                                    # data.location = stock_move_line.location_id.name
                                    product_dict[r1.product_id.id] = data
                                else:
                                    object = comparebymonth()
                                    object.current_month_total_qty = stock_move_line.qty_done
                                    object.current_month_total_amount = r1.price_unit * stock_move_line.qty_done
                                    object.product_name = r1.product_id.name
                                    object.sku = r1.product_id.product_tmpl_id.sku_code
                                    # object.location = stock_move_line.location_id.name
                                    product_dict[r1.product_id.id] = object

        for record in filtered_by_last_month:
            stock_picking = self.env['stock.picking'].search([('sale_id', '=', record.id)])
            if len(stock_picking) == 1:
                for r1 in record.order_line:
                    stock_move = self.env['stock.move'].search([('picking_id', '=', stock_picking.id), ('product_id', '=', r1.product_id.id),('state', 'in', ('done', 'partially_available'))])
                    if len(stock_move) == 1:
                        stock_move_line = self.env['stock.move.line'].search(
                            [('move_id', '=', stock_move.id), ('state', 'in', ('done', 'partially_available'))])
                        if len(stock_move_line) == 1:
                            if int(stock_move_line.qty_done) > 0:
                                if r1.product_id.id in product_dict:
                                    data = product_dict[r1.product_id.id]
                                    data.last_month_total_qty = data.last_month_total_qty + stock_move_line.qty_done
                                    data.last_month_total_amount = data.last_month_total_amount + (r1.price_unit * stock_move_line.qty_done)
                                    # data.location = stock_move_line.location_id.name
                                    product_dict[r1.product_id.id] = data
                                else:
                                    object = comparebymonth()
                                    object.last_month_total_qty = stock_move_line.qty_done
                                    object.last_month_total_amount = r1.price_unit * stock_move_line.qty_done
                                    object.product_name = r1.product_id.name
                                    object.sku = r1.product_id.product_tmpl_id.sku_code
                                    # object.location = stock_move_line.location_id.name
                                    product_dict[r1.product_id.id] = object
        return product_dict
