# See LICENSE file for full copyright and licensing details.

import werkzeug
from odoo import fields, http
from odoo.http import request
from datetime import datetime
from werkzeug.exceptions import Forbidden, NotFound
from odoo.tools import lazy
from odoo import fields, http, SUPERUSER_ID, tools
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.website_sale.controllers.main import TableCompute, QueryURL

PPG = 20
PPR = 4

class WebsiteSale(WebsiteSale):

    # def _search_get_detail
    def _get_search_options( self, category=None, attrib_values=None, pricelist=None, min_price=0.0, max_price=0.0, conversion_rate=1, **post):
        vals = super(WebsiteSale,self)._get_search_options(category=category, attrib_values=attrib_values, pricelist=pricelist, min_price=min_price, max_price=max_price, conversion_rate=conversion_rate, **post)
        vals.update({
            'brand': post.get('brand')
        })
        return vals

    @http.route(['/page/<int:page>', '/shop/brands'], type='http', auth='public', website=True)
    def shopBrand(self, page=0, category=None, search='', brand=None, min_price=0.0, max_price=0.0, ppg=False, **post):
        post.update({'brand': brand and int(brand) or 0})
        return super(WebsiteSale,self).shop(page=page, category=category, search=search, min_price=min_price, max_price=max_price, ppg=ppg, **post)

    # def currency_compute(self, from_currency, to_currency):
    #     return lambda price: from_currency.compute(price,
    #                                                to_currency)

    # Method to get the brands.
    @http.route(['/page/product_brands'], type='http', auth='public',
                website=True)
    def product_brands(self, **post):
        brand_values = []
        brand_obj = request.env['product.brand']
        domain = []
        if post.get('search'):
            domain += [('name', 'ilike', post.get('search'))]
        brand_ids = brand_obj.search(domain)
        for brand_rec in brand_ids:
            brand_values.append(brand_rec)

        keep = QueryURL('/page/product_brands', brand_id=[])
        values = {'brand_rec': brand_values, 'keep': keep}
        if post.get('search'):
            values.update({'search': post.get('search')})
        return request.render('website_product_brand.product_brands', values)
