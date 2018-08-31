from odoo import models, fields, api
import logging
from operator import itemgetter

_logger = logging.getLogger(__name__)


class AvailableProductList(models.TransientModel):
    _name = "available.product.list"

    available_production_lot_list_to_be_returned = []

    # get available production lot list, parameter product id.
    def get_available_production_lot_list(self):
        production_lot_list = self.env['stock.quant'].search([('quantity', '>', 0), ('location_id.usage', '=', 'internal'), ('location_id.active', '=', 'true')])

        for production_lot in production_lot_list:
            if production_lot.id and production_lot.lot_id and production_lot.product_id and production_lot.quantity and production_lot.lot_id.use_date:
                available_product = dict(stock_quant_id = production_lot.id,
                                        lot_id = production_lot.lot_id,
                                        product_id = production_lot.product_id,
                                        available_quantity = production_lot.quantity,
                                        reserved_quantity = production_lot.reserved_quantity,
                                        use_date = production_lot.lot_id.use_date)

                self.available_production_lot_list_to_be_returned.append(available_product)
        # sort list by latest expiry date(life date)
        available_production_lot_list_to_be_returned = sorted(self.available_production_lot_list_to_be_returned, key=itemgetter('use_date'))
        return available_production_lot_list_to_be_returned

    def update_production_lot_list(self):
        _logger.info('In update db()')

        for production_lot in self.available_production_lot_list_to_be_returned:
            updated_dict = {'quantity': production_lot['available_quantity'],
                            'reserved_quantity': production_lot['reserved_quantity']}
            self.env['stock.quant'].search([('id', '=', production_lot['stock_quant_id'])]).write(
                 dict(updated_dict))
