# -*- coding: utf-8 -*-
import odoo
import json
import logging
from odoo import fields, http
from odoo.http import request

_logger = logging.getLogger(__name__)

class WebsiteSales(odoo.addons.website_sale.controllers.main.WebsiteSale):
    @http.route([
        '/shop',
        '/shop/featured',
        '/shop/capital-equipment',
        '/shop/page/<int:page>',
        '/shop/category/<model("product.public.category"):category>',
        '/shop/category/<model("product.public.category"):category>/page/<int:page>'
    ], type='http', auth="public", website=True)
    def shop(self, page=0, category=None, search='', ppg=False, **post):
        product_template = request.env['product.template'].search([('actual_quantity', '=', False)])
        if len(product_template)>0:
            for product in product_template:
                product.update({'actual_quantity':0})

        if not 'order' in post:
            post.update({'order': 'actual_quantity desc'})

        if request.httprequest.path == "/shop/featured":
            result = request.env['product.public.category'].search([('name', 'ilike', 'featured')], limit=1)
            if result:
                category = result.id

        if request.httprequest.path == "/shop/capital-equipment":
            result = request.env['product.public.category'].search([('name', 'ilike', 'capital equipment')], limit=1)
            if result:
                category = result.id

        responce = super(WebsiteSales, self).shop(page, category, search, ppg, **post)

        payload = responce.qcontext
        irConfig = request.env['ir.config_parameter'].sudo()
        payload['isVisibleWebsiteExpirationDate'] = irConfig.get_param('website_sales.website_expiration_date')
        if payload['products'] and payload['isVisibleWebsiteExpirationDate']:
            productProduct = request.env['product.product'].search([('product_tmpl_id', 'in', payload['products'].ids)])

            productMaxMinDates = {}
            for val in productProduct:
                if (val.actual_quantity) > 0:
                    query_result = self.fetch_lot_expirydates(val.id)
                    productMaxMinDates[val.id] = {"min": fields.Datetime.from_string(query_result['min']),
                                                  "max": fields.Datetime.from_string(query_result['max'])}
                else:
                    productMaxMinDates[val.id] = {
                        "min": None,
                        "max": None
                    }

            payload['productExpiration'] = productMaxMinDates

        porductRows = [[]]
        i = 1
        for val in payload['products']:
            porductRows[-1].append(val)
            if i % 4 == 0:
                porductRows.append([])
            i += 1

        payload['porductRows'] = porductRows

        return request.render("website_sale.products", payload)

    @http.route(['/shop/product/<model("product.template"):product>'], type='http', auth="public", website=True)
    def product(self, product, category='', search='', **kwargs):
        responce = super(WebsiteSales, self).product(product, category='', search='', **kwargs)
        payload = responce.qcontext

        productMaxMinDates = {}
        if (payload['product'].actual_quantity) > 0:
            query_result = self.fetch_lot_expirydates(payload['product'].product_variant_id.id)
            productMaxMinDates[payload['product'].product_variant_id.id] = {
                "min": fields.Datetime.from_string(query_result['min']),
                "max": fields.Datetime.from_string(query_result['max'])
            }
        else:
            productMaxMinDates[payload['product'].product_variant_id.id] = {
                "min": None,
                "max": None
            }

        payload['productExpiration'] = productMaxMinDates
        payload['userEmail'] = request.env.user.email
        payload['isVisibleWebsiteExpirationDate'] = request.env['ir.config_parameter'].sudo().get_param(
            'website_sales.website_expiration_date')
        return request.render("website_sale.product", payload)

    def fetch_lot_expirydates(self, product_id):
        request.env.cr.execute(
            """SELECT
                sum(quantity), min(use_date), max(use_date)
            FROM
                stock_quant
            INNER JOIN
                stock_production_lot
            ON
                (
                    stock_quant.lot_id = stock_production_lot.id)
            INNER JOIN
                stock_location
            ON
                (
                    stock_quant.location_id = stock_location.id)
            WHERE
                stock_location.usage in('internal', 'transit') and stock_production_lot.product_id = %s """,
            (product_id,))
        return request.env.cr.dictfetchone()

    @http.route(['/shop/confirmation'], type='http', auth="public", website=True)
    def payment_confirmation(self, **post):
        responce = super(WebsiteSales, self).payment_confirmation(**post)
        order = responce.qcontext['order']
        order.workflow_process_id = 1

        template = request.env.ref('website_sales.website_order_placed').sudo()

        if request.env.user.user_id.id and not request.env.user.user_id.id == order.user_id.id:
            order.user_id = request.env.user.user_id

        template.send_mail(order.id, force_send=True)
        msg = "Quotation Email Sent to: " + order.user_id.login
        order.message_post(body=msg)


        return responce

    @http.route(['/shop/quote_my_report/update_json'], type='json', auth="public", methods=['POST'], website=True)
    def update_quote_my_report_json(self, product_id, new_qty=None):
        count = 1
        print('In update_quote_my_report_json')
        print(product_id)
        print(new_qty)
        request.env['quotation.product.list'].sudo().update_quantity(product_id, new_qty)
        # product_list = request.env['quotation.product.list'].sudo().search([('partner', '=', int(partner_id))])
        # print('product_list')
        # print(product_list)
        # for res in product_list:
        #     print(res.product)
        # request.env['quotation.product.list'].update_record(int(product_id), int(partner_id), int(set_qty))
        return count

    @http.route(['/shop/quote_my_report/<int:partner_id>'], type='http', auth="public", website=True)
    def quote_my_report(self, partner_id):
        _logger.info('In quote my report')
        return request.redirect('/web/login')
        # margins_context = {'quote_my_report_partner_id': partner_id}
        # request.env['quotation.product.list'].with_context(margins_context).sudo().delete_and_create()
        #
        # product_list = request.env['quotation.product.list'].sudo().get_product_list()
        #
        # return http.request.render('website_sales.quote_my_report', {'product_list': product_list})

    @http.route(['/add/product/cart'], type='http', auth="public", website=True)
    def add_product_in_cart(self):
        print('add product in cart')
        product_list = request.env['quotation.product.list'].sudo().get_product_list()
        print('product list')
        print(product_list)
        for product_id in product_list:
            if product_list.get(product_id)[0]['quantity'] > 0:
                print(product_list.get(product_id)[0]['product'].id)
                self.cart_update_custom(product_list.get(product_id)[0]['product'].id,
                                    product_list.get(product_id)[0]['quantity'])
        return request.redirect("/shop/cart")


    @http.route(['/shop/quote_my_report_authentication/<int:partner_id>'], type='http', auth="public", website=True)
    def quote_my_report_authentication(self, partner_id):
        _logger.info('In quote my report authentication %s', partner_id)
        if request.session.uid:
            _logger.info('Login successfully')
            user = request.env['res.users'].search([('id', '=', request.session.uid)])
            if user and user.partner_id and user.partner_id.id == partner_id:
                sales = request.env['sale.order'].sudo().search([('partner_id', '=', partner_id)])
                products = {}
                for sale in sales:
                    sale_order_lines = request.env['sale.order.line'].sudo().search([('order_id', '=', sale.id)])
                    for line in sale_order_lines:
                        # _logger.info(" product_id qty_available %r", line.product_id.actual_quantity)
                        if line.product_id.actual_quantity and line.product_id.actual_quantity is not None and line.product_id.actual_quantity > 0 and line.product_id.product_tmpl_id.sale_ok:
                            products[line.product_id] = line.product_id

                for product in products:
                    self.cart_update_custom(product.id)
            else:
                request.session['invalid_url_message'] = 'The requested URL is not valid for logged in user.'
        return request.redirect("/shop/cart")

    # share_link = partner._get_signup_url_for_action(action='/mail/view', res_id=self.res_id, model=self.model)[partner.id]

    def cart_update_custom(self, product_id, add_qty, set_qty=0, **kw):
        """This route is called when adding a product to cart (no options)."""
        sale_order = request.website.sale_get_order(force_create=True)
        if sale_order.state != 'draft':
            request.session['sale_order_id'] = None
            sale_order = request.website.sale_get_order(force_create=True)

        product_custom_attribute_values = None
        if kw.get('product_custom_attribute_values'):
            product_custom_attribute_values = json.loads(kw.get('product_custom_attribute_values'))

        no_variant_attribute_values = None
        if kw.get('no_variant_attribute_values'):
            no_variant_attribute_values = json.loads(kw.get('no_variant_attribute_values'))

        sale_order._cart_update(
            product_id=int(product_id),
            add_qty=add_qty,
            set_qty=set_qty,
            product_custom_attribute_values=product_custom_attribute_values,
            no_variant_attribute_values=no_variant_attribute_values
        )

    @http.route(['/shop/cart'], type='http', auth="public", website=True, sitemap=False)
    def cart(self, access_token=None, revive='', **post):
        responce = super(WebsiteSales, self).cart(access_token=None, revive='', **post)
        values = responce.qcontext
        if 'invalid_url_message' in request.session and request.session.get('invalid_url_message') != '':
            values['invalid_url'] = request.session.get('invalid_url_message')
            request.session.pop('invalid_url_message')
        return request.render("website_sale.cart", values)


class WebsiteSaleOptionsCstm(odoo.addons.website_sale.controllers.main.WebsiteSale):
    @http.route(['/shop/modal'], type='json', auth="public", methods=['POST'], website=True)
    def modal(self, product_id, **kw):
        pricelist = request.website.get_current_pricelist()
        product_context = dict(request.context)
        quantity = kw['kwargs']['context']['quantity']
        if not product_context.get('pricelist'):
            product_context['pricelist'] = pricelist.id
        # fetch quantity from custom context
        product_context.update(kw.get('kwargs', {}).get('context', {}))

        from_currency = request.env.user.company_id.currency_id
        to_currency = pricelist.currency_id
        compute_currency = lambda price: request.env['res.currency']._compute(from_currency, to_currency, price)
        product = request.env['product.product'].with_context(product_context).browse(int(product_id))

        main_product_attr_ids = self.get_attribute_value_ids(product)
        for variant in main_product_attr_ids:
            if variant[0] == product.id:
                # We indeed need a list of lists (even with only 1 element)
                main_product_attr_ids = [variant]
                break

        return request.env['ir.ui.view'].render_template("website_sales.modalCSTM", {
            'product': product,
            'quantity': quantity,
            'compute_currency': compute_currency,
            'get_attribute_value_ids': self.get_attribute_value_ids,
            'main_product_attr_ids': main_product_attr_ids,
        })
