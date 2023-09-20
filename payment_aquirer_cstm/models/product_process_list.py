# -*- coding: utf-8 -*-

from odoo.http import request
from odoo import api, fields, models, tools, SUPERUSER_ID, _

class product_process_list(models.Model):
    _name = "product.process.list"
    _description = "Online Product Qty "

    product_id = fields.Many2one('product.product', 'Product')
    so_name = fields.Char(string='SO name')
    process_qty = fields.Integer(string='Process Qty')
    customer_id = fields.Many2one('res.partner', string='Customer')


    def is_product_in_process(self, product_id,so_name):
        records = self.search([('product_id', '=', product_id.id),('so_name', '=', so_name)])
        return True if len(records) > 0 else False

    def get_product_process_qty_by_product(self, product_id):
        records = self.search([('product_id', '=', product_id.id)])
        sum = 0
        for rec in records:
            sum += rec.process_qty
        return sum

    def remove_recored_by_product_and_so(self, product_id, so_name):
        record = self.search([('product_id', '=', product_id.id),('so_name', '=', so_name)], limit=1)
        return record.unlink()