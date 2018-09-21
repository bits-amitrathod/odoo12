# -*- coding: utf-8 -*-
import json
import logging
from werkzeug.exceptions import Forbidden, NotFound

from odoo import http, tools, _
from odoo.http import request
from odoo.addons.base.ir.ir_qweb.fields import nl2br
from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.website.controllers.main import QueryURL
from odoo.exceptions import ValidationError
from odoo.addons.website.controllers.main import Website
from odoo.addons.website_form.controllers.main import WebsiteForm
from odoo.osv import expression

_logger = logging.getLogger(__name__)
class WebsiteSale(http.Controller):

    @http.route(['/shop/engine/update_json'], type='json', auth="public", methods=['POST'], website=True, csrf=False)
    def cart_update_json(self, quote_id,product_id, line_id=None, add_qty=None, set_qty=None, display=True):
        order = request.website.sale_get_engine_order(quote_id,force_create=1)
        print("Inside Controller");
        print(order.state);
        if order.state != 'sent':
            request.website.sale_reset()
            return {}
        '''value = order._cart_update(product_id=product_id, line_id=line_id, add_qty=add_qty, set_qty=set_qty)
        print(value);
        if not order.cart_quantity:
            request.website.sale_reset()
            return value

        order = request.website.sale_get_order()
        value['cart_quantity'] = order.cart_quantity
        from_currency = order.company_id.currency_id
        to_currency = order.pricelist_id.currency_id

        if not display:
            return value

        value['website_sale.cart_lines'] = request.env['ir.ui.view'].render_template("website_sale.cart_lines", {
            'website_sale_order': order,
            'compute_currency': lambda price: from_currency.compute(price, to_currency),
            'suggested_products': order._cart_accessories()
        })'''
        return {}