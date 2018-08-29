from odoo import models, fields
import logging

_logger = logging.getLogger(__name__)


class AllocatedProductList(models.Model):
    _name = "allocated.product.list"

    customer_id = fields.Integer(store= False)
    product_id = fields.Integer(store= False)
    allocated_product_quantity = fields.Integer(store= False)

    def add_allocated_products(self, customer_id, product_id, allocated_product_quantity):
        self.customer_id = customer_id
        self.product_id = product_id
        self.allocated_product_quantity = allocated_product_quantity

    def display_allocated_products(self, allocated_product_list):
        _logger.info('In display allocated product list %r' , allocated_product_list)