from odoo import models, fields
import logging

_logger = logging.getLogger(__name__)


class AllocatedProductList(models.TransientModel):
    _name = "allocated.product.list"

    customer_id = fields.Integer()
    product_id = fields.Integer()
    allocated_product_quantity = fields.Integer()

    allocated_list = []

    def add_allocated_products(self, customer_id, product_id, allocated_product_quantity):
        allocated_product = self.pool.get('allocated.product.list')
        allocated_product.customer_id = customer_id
        allocated_product.product_id = product_id
        allocated_product.allocated_product_quantity = allocated_product_quantity
        self.allocated_list.append(allocated_product)


    def display_allocated_product_list(self):
        for product in self.allocated_list:
            _logger.info('In display allocated product list %r, %r', str(product.product_id), str(product.allocated_product_quantity))