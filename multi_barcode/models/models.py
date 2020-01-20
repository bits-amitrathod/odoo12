# -*- coding: utf-8 -*-

from odoo import models, fields, api

class multi_barcode(models.Model):
    _name = 'multi.barcode'
    # _inherit = 'product.product'

    product_id = fields.Many2one('product.template', readonly=False)
    barcode = fields.Char('Barcode', copy=False, oldname='ean13',
        help="International Article Number used for product identification.")

    #
    # @api.model
    # def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
    #     sup_return = super(multi_barcode, self)._name_search(name, args=None, operator='ilike', limit=100, name_get_uid=None)
    #     product_ids = self._search([(self.barcode, '=', name)] + args, limit=limit, access_rights_uid=name_get_uid)
    #     return sup_return
