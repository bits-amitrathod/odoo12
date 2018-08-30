from odoo import models, fields, api
import logging
from operator import attrgetter

_logger = logging.getLogger(__name__)

available_production_lot_list_to_be_returned = []


class AvailableProductList(models.TransientModel):
    _name = "available.product.list"

    stock_quant_id = fields.Integer()
    lot_id = fields.Integer()
    product_id = fields.Integer()
    available_quantity = fields.Boolean()
    reserved_quantity = fields.Boolean()
    use_date = fields.Date() # product expiry date


    # get available production lot list, parameter product id.
    def get_available_production_lot_list(self):
        production_lot_list = self.env['stock.quant'].search(
            [('quantity', '>', 0), ('location_id.usage', '=', 'internal'), ('location_id.active', '=', 'true')])

        for production_lot in production_lot_list:
            available_product = self.pool.get('available.product.list')

            if production_lot.id and production_lot.lot_id and production_lot.product_id and production_lot.quantity and production_lot.lot_id.use_date:

                available_product.stock_quant_id = production_lot.id
                available_product.lot_id = production_lot.lot_id
                available_product.product_id = production_lot.product_id
                available_product.available_quantity = production_lot.quantity
                available_product.reserved_quantity = production_lot.reserved_quantity
                available_product.use_date = production_lot.lot_id.use_date

                available_production_lot_list_to_be_returned.append(available_product)
        # sort list by latest expiry date(life date)
        available_production_lot_list_to_be_returned.sort(key=attrgetter('use_date'))
        return available_production_lot_list_to_be_returned

    def update_production_lot_list(self):
        _logger.info('In update db()')

        remaining_production_lot_list = available_production_lot_list_to_be_returned

        for production_lot in remaining_production_lot_list:
            updated_dict = {'quantity': production_lot.available_quantity,
                            'reserved_quantity': production_lot.reserved_quantity}
            self.env['stock.quant'].search([('id', '=', production_lot.stock_quant_id)]).write(
                 dict(updated_dict))
