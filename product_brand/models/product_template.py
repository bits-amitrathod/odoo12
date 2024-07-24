# Copyright 2009 NetAndCo (<http://www.netandco.net>).
# Copyright 2011 Akretion Benoît Guillot <benoit.guillot@akretion.com>
# Copyright 2014 prisnet.ch Seraphine Lantible <s.lantible@gmail.com>
# Copyright 2016 Serpent Consulting Services Pvt. Ltd.
# Copyright 2018 Daniel Campos <danielcampos@avanzosc.es>
# Copyright 2019 Kaushal Prajapati <kbprajapati@live.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models, api

class ProductTemplate(models.Model):
    _inherit = "product.template"

    product_brand_id = fields.Many2one("product.brand", string="Brand", help="Select a brand for this product")
    list_price = fields.Float('Sales Price', default=1.0, digits='Product Price', help="Price at which the product is sold to customers.", tracking=True)
    active = fields.Boolean('Active', default=True, help="If unchecked, it will allow you to hide the product without removing it.", tracking=True)

    @api.model
    def _search_get_detail(self, website, order, options):
        res = super(ProductTemplate, self)._search_get_detail(website, order, options)
        domains = res.get('base_domain')
        brand = options.get('brand')
        if brand:
            domains.append([('product_brand_id', 'in', [int(brand)])])
