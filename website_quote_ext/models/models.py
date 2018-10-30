# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class Website(models.Model):
    _inherit = 'website'

    @api.multi
    def sale_get_engine_order(self, order_id,line_id,set_qty,product_id):

        _logger.info((self.env['sale.order'].search([('id', '=', order_id)])))
        order = self.env['sale.order'].search([('id', '=', order_id)])[0]
        values = {'product_uom_qty':set_qty}
        line = self.env['sale.order.line'].sudo().search([('id', '=', line_id)])[0]
        line.write(values)
        move = self.env['stock.move'].search([('sale_line_id', '=', line_id)])
        _logger.info("move")
        _logger.info(move)
        moveline = self.env['stock.move.line'].search([('move_id', '=', move.id)])
        _logger.info("moveline")
        _logger.info(moveline)
        moveline.write(values)
        _logger.info(moveline)
        #order.write(line)
        count = self.env['prioritization.engine.model'].get_available_product_count(order.partner_id.id, product_id)
        return count;

    @api.multi
    def sale_get_engine_count(self, order_id,product_id):
        order = self.env['sale.order'].search([('id', '=', order_id)])[0]
        count = self.env['prioritization.engine.model'].get_available_product_count(order.partner_id.id, product_id)
        return count;

