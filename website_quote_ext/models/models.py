# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class Website(models.Model):
    _inherit = 'website'

    @api.multi
    def sale_get_engine_order(self, order_id,line_id,set_qty,product_id):
        _logger.info("inside sale_get_engine_order")
        order = self.env['sale.order'].search([('id', '=', order_id)])[0]
        values = {'product_uom_qty':set_qty}
        line = self.env['sale.order.line'].sudo().search([('id', '=', line_id)])[0]
        line.write(values)
        move = self.env['stock.move'].search([('sale_line_id', '=', line_id)])
        _logger.info(move.move_line_ids)
        for movelineid in move.move_line_ids:
            _logger.info("Inside First For")
            _logger.info(movelineid)
            moveline = self.env['stock.move.line'].search([('id', '=', movelineid)])
            _logger.info(moveline.package_id)
            _logger.info(moveline.result_package_id)
            package=self.env['stock.quant.package'].search([('id', '=', moveline.package_id)])
            _logger.info(package.quant_ids)
            quants=self.env['stock.quant'].search([('id', '=', package.quant_ids)])
            for quant in quants:
                _logger.info("Inside second For")
                _logger.info(quant)
                value = {'quantity':quant.quantity-1,'reserved_quantity': set_qty}
                quant.write(value)
                _logger.info(quant)
        #order.write(line)
        count = self.env['prioritization.engine.model'].get_available_product_count(order.partner_id.id, product_id)
        return count;

    @api.multi
    def sale_get_engine_count(self, order_id,product_id):
        order = self.env['sale.order'].search([('id', '=', order_id)])[0]
        count = self.env['prioritization.engine.model'].get_available_product_count(order.partner_id.id, product_id)
        return count;

