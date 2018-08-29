# -*- coding: utf-8 -*-
# © 2009 NetAndCo (<http://www.netandco.net>).
# © 2011 Akretion Benoît Guillot <benoit.guillot@akretion.com>
# © 2014 prisnet.ch Seraphine Lantible <s.lantible@gmail.com>
# © 2016-Today Serpent Consulting Services Pvt. Ltd.
#    (<http://www.serpentcs.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class ProductBrand(models.Model):
    _name = 'product.brand'

    name = fields.Char('Manufacture Name', related='partner_id.name',readonly=True,store=True)
    description = fields.Text('Description', translate=True)
    manufacturer_pname = fields.Char(string='Manuf. Product Name')
    manufacturer_purl = fields.Char(string='Manuf. Product URL')
    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        help='Select a partner for this Manufacture if any.',
        ondelete='restrict',required=True
    )
    logo = fields.Binary('Logo File')
    product_ids = fields.One2many(
        'product.template',
        'product_brand_id',
        string='Manufacture Products',
    )
    products_count = fields.Integer(
        string='Number of products',
        compute='_get_products_count',
    )

    @api.multi
    @api.depends('product_ids')
    def _get_products_count(self):
        self.products_count = len(self.product_ids)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    product_brand_id = fields.Many2one(
        'product.brand',
        string='Manufacture',
        help='Select a Manufacture for this product'
    )
