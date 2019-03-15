from odoo import models, fields, api
import logging
from datetime import date
from operator import itemgetter

_logger = logging.getLogger(__name__)


class AvailableProductDict(models.TransientModel):
    _name = "available.product.dict"

    available_production_lot_dict_to_be_returned = {}

    # get available production lot list, parameter product id.
    def get_available_production_lot_dict(self):
        self.available_production_lot_dict_to_be_returned.clear()
        production_lot_list = self.env['stock.quant'].search([('quantity', '>', 0), ('location_id.usage', '=', 'internal'), ('location_id.active', '=', 'true'), ('lot_id.use_date', '>', str(date.today()))])

        for production_lot in production_lot_list:
            if production_lot.id and production_lot.lot_id and production_lot.product_id and production_lot.quantity and production_lot.lot_id.use_date and not production_lot.lot_id.use_date is None:
                available_quantity = production_lot.quantity - production_lot.reserved_quantity
                if available_quantity > 0:
                    available_product = {production_lot.lot_id.id : {'stock_quant_id':production_lot.id,
                                            'available_quantity':available_quantity,
                                            'reserved_quantity':production_lot.reserved_quantity,
                                            'use_date':production_lot.lot_id.use_date,
                                            'lot_id': production_lot.lot_id}}
                    if production_lot.product_id.id in self.available_production_lot_dict_to_be_returned.keys():
                        self.available_production_lot_dict_to_be_returned.get(production_lot.product_id.id,{}).append(available_product)
                    else:
                        dict = {production_lot.product_id.id: [available_product]}
                        self.available_production_lot_dict_to_be_returned.update(dict)

        # sort list by latest expiry date(use date)
        #available_production_lot_list_to_be_returned = sorted(self.available_production_lot_list_to_be_returned, key=itemgetter('use_date'))
        return self.available_production_lot_dict_to_be_returned

    def update_production_lot_dict(self):
        _logger.debug('In update db() %r', self.available_production_lot_dict_to_be_returned)

        for product_id_key in self.available_production_lot_dict_to_be_returned.keys():
            for available_production_lot in self.available_production_lot_dict_to_be_returned.get(product_id_key, {}):
                updated_dict = {'quantity': available_production_lot.get(list(available_production_lot.keys()).pop(0), {})['available_quantity'],
                                'reserved_quantity': available_production_lot.get(list(available_production_lot.keys()).pop(0), {})['reserved_quantity']}

                stock_quant = self.env['stock.quant'].search([('id', '=', available_production_lot.get(list(available_production_lot.keys()).pop(0), {})['stock_quant_id'])])
                stock_quant.write(dict(updated_dict))

    def get_available_production_lot(self):
        available_production_lot_dict={}
        production_lot_list = self.env['stock.quant'].search(
            [('quantity', '>', 0), ('location_id.usage', '=', 'internal'), ('location_id.active', '=', 'true'), ('lot_id.use_date', '>', str(date.today()))])

        for production_lot in production_lot_list:
            if production_lot.id and production_lot.lot_id and production_lot.product_id and production_lot.quantity and production_lot.lot_id.use_date:
                available_quantity = production_lot.quantity - production_lot.reserved_quantity
                if available_quantity > 0:
                    available_product = {production_lot.lot_id.id: {'stock_quant_id': production_lot.id,
                                                                    'available_quantity': available_quantity,
                                                                    'reserved_quantity': production_lot.reserved_quantity,
                                                                    'use_date': production_lot.lot_id.use_date}}

                    if production_lot.product_id.id in available_production_lot_dict.keys():
                        available_production_lot_dict.get(production_lot.product_id.id,{}).append(available_product)
                    else:
                        dict = {production_lot.product_id.id: [available_product]}
                        available_production_lot_dict.update(dict)

        # sort list by latest expiry date(use date)
        # available_production_lot_list_to_be_returned = sorted(self.available_production_lot_list_to_be_returned, key=itemgetter('use_date'))
        return available_production_lot_dict
