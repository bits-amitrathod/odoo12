# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools


class TempProductList(models.TransientModel):
    _name = 'temp.product.list'
    # _auto = False

    quantity = fields.Integer(string='Quantity')
    product = fields.Many2one('product.product', string='Product')
    partner = fields.Many2one('res.partner', string="Partner")

    _sql_constraints = [
        ('product_uniq', 'unique(product, partner)', 'product must be unique per partner!'),
    ]

    # @api.model_cr
    # def init(self):
    #     print('In init')
    #     self.init_table()
    #
    # def init_table(self):
    #     print('In table')
    #     self._cr.execute("DROP TABLE IF EXISTS temp_product_list")
    #     # tools.drop_view_if_exists(self._cr, self._name.replace(".", "_"))
    #
    # @api.model_cr
    # def delete_and_create(self):
    #     print('In delete and create')
    #     self.init_table()

    # def save_record(self, product_id, partner_id):
    #     print('In save_record')
    #     print(product_id)
    #     print(partner_id)
    #     self.create({'product_id': product_id, 'partner_id': partner_id})
    #
    # def get_saved_record(self):
    #     print('In get_saved_record')
    #     for ss in self:
    #         print(ss)