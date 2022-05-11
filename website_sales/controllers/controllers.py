# -*- coding: utf-8 -*-
import odoo
import json
import logging
from odoo import fields, http
from odoo.http import request
from odoo.addons.http_routing.models.ir_http import slug

_logger = logging.getLogger(__name__)

class WebsiteSales(odoo.addons.website_sale.controllers.main.WebsiteSale):
    @http.route([
        '/shop',
        '/shop/featured',
        '/shop/capital-equipment',
        '/shop/page/<int:page>',
        '/shop/category/<model("product.public.category"):category>',
        '/shop/category/<model("product.public.category"):category>/page/<int:page>',
        '/shop/category/<model("product.public.category"):category>/brand/<model("product.brand"):brand>',
        '/shop/category/<model("product.public.category"):category>/brand/<model("product.brand"):brand>/page/<int:page>',
        '/shop/brand/<model("product.brand"):brand>',
        '/shop/brand/<model("product.brand"):brand>/page/<int:page>'
    ], type='http', auth="public", website=True)
    def shop(self, page=0, category=None,search='', brand= None, ppg=False, **post):
        product_template = request.env['product.template'].search([('actual_quantity', '=', False)])
        product_brands = []

        title = "Shop Surgical Surplus"
        sub_title = "Browse Discount Surgical Surplus in our Online Store"
        c_all_id = request.env['product.public.category'].search([('name', 'ilike', 'All')], limit=1)
        if request.httprequest.path == "/shop":
            result = c_all_id
            if result:
                category = result

        if len(product_template)>0:
            for product in product_template:
                product.update({'actual_quantity':0})

        if ppg:
            try:
                ppg = int(ppg)
                post['ppg'] = ppg
            except ValueError:
                ppg = False
        if not ppg:
            ppg = 20

        if not 'order' in post:
            post.update({'order': 'actual_quantity desc'})

        if request.httprequest.path == "/shop/featured":
            title = "Discount Surgical Supplies"
            sub_title = "Shop Sale Surgical Products"
            result = request.env['product.public.category'].search([('name', 'ilike', 'featured')], limit=1)
            if result:
                category = result

        if request.httprequest.path == "/shop/capital-equipment":
            title = "Surplus Surgical Equipment"
            sub_title = "Shop Surplus Surgical Equipment"
            result = request.env['product.public.category'].search([('name', 'ilike', 'surgical equipment')], limit=1)
            if result:
                category = result

        #  after category id Found the find Brand List
        if category:
            if str(c_all_id.id) == str(category) if isinstance(category, str) else str(category.id) :
                product_brands = request.env['product.brand'].search([])
            else:
                s = str(category) if isinstance(category, str) else str(category.id)
                request.env.cr.execute("SELECT product_template_id FROM product_public_category_product_template_rel where product_public_category_id = "+ s)
                r = request.env.cr.fetchall()
                pt_list = request.env['product.template'].sudo().search([('id', 'in', r)])
                for b in pt_list:
                    if b.product_brand_id:
                        if not b.product_brand_id in product_brands:
                            product_brands.append(b.product_brand_id)

        responce = super(WebsiteSales, self).shop(page, category, search, None, **post)

        payload = responce.qcontext

        if brand:
            search_product =[]
            url = "/shop/category/"+slug(category)+"/brand/%s" % slug(brand)
            if category:
                request.env.cr.execute(
                    "SELECT product_template_id FROM product_public_category_product_template_rel where product_public_category_id = " + str(
                        category.id))
                r = request.env.cr.fetchall()
                pt_list_b = request.env['product.template'].sudo().search([('id', 'in', r),('product_brand_id','=',brand.id)])
            search_product = pt_list_b
            product_count = len(search_product)
            pager = request.website.pager(url=url, total=product_count, page=page, step=ppg, scope=7, url_args=post)
            payload['pager'] = pager
            offset = pager['offset']
            products = search_product[offset: offset + ppg]
            payload['products'] = products

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
            # if i % 4 == 0:
            #     porductRows.append([])
            # i += 1

        payload['porductRows'] = porductRows
        payload['brands'] = product_brands
        payload['brand_id']= int(brand.id) if brand else 0
        payload['title'] = title
        payload['sub_title'] = sub_title
        return request.render("website_sale.products", payload)

    # Compatibility pre-v14
    # @http.route(['/shop/product/<model("product.template"):product>'], type='http', auth="public", website=True)
    @http.route(['/shop/<model("product.template"):product>'], type='http', auth="public", website=True, sitemap=True)
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

    # @http.route(['/shop/confirmation'], type='http', auth="public", website=True)
    @http.route(['/shop/confirmation'], type='http', auth="public", website=True, sitemap=False)
    def payment_confirmation(self, **post):
        _logger.info('start In payment_confirmation')
        responce = super(WebsiteSales, self).payment_confirmation(**post)
        order = responce.qcontext['order']
        order.workflow_process_id = 1

        _logger.info('- sale_order_no: %s', order.name)
        _logger.info('- workflow_id : %s', order.workflow_process_id)
        if order.workflow_process_id:
            _logger.info('- workflow_name : %s', order.workflow_process_id.name)

        template = request.env.ref('website_sales.website_order_placed').sudo()

        if request.env.user.user_id.id and not request.env.user.user_id.id == order.user_id.id:
            order.user_id = request.env.user.user_id
        template.email_from ='info@surgicalproductsolutions.com'
        template.send_mail(order.id, force_send=False)
        msg = "Quotation Email Sent to: " + order.user_id.login
        order.message_post(body=msg)
        _logger.info('End In payment_confirmation')
        return responce

    @http.route(['/shop/quote_my_report/update_json'], type='json', auth="public", methods=['POST'], website=True)
    def update_quote_my_report_json(self, partner_id=None, product_id=None, new_qty=None, select=None):
        count = 1
        if partner_id is None:
            if request.session.uid:
                user = request.env['res.users'].search([('id', '=', request.session.uid)])
                if user and user.partner_id and user.partner_id.id:
                    partner_id = user.partner_id.id
        request.env['quotation.product.list'].sudo().update_quantity(partner_id, product_id, new_qty, select)
        return count

    @http.route(['/shop/quote_my_report/update_json_list'], type='json', auth="public", methods=['POST'], website=True)
    def update_quote_my_report_json_list(self, partner_id=None, product_id=None, new_qty=None, select=None):
        count = 1
        _logger.info('- update_quote_my_report_json_list  partner_id id : %s', partner_id)
        _logger.info('- update_quote_my_report_json_list  product_id id : %s', product_id)
        _logger.info('- update_quote_my_report_json_list  new_qty id : %s', new_qty)
        if partner_id is None:
            if request.session.uid:
                user = request.env['res.users'].search([('id', '=', request.session.uid)])
                if user and user.partner_id and user.partner_id.id:
                    partner_id = user.partner_id.id
        for i in range(0, len(product_id)):
            request.env['quotation.product.list'].sudo().update_quantity_from_list(partner_id, product_id[i], new_qty[i], True)
        return count

    @http.route(['/shop/my_in_stock_report'], type='http', auth="public", website=True)
    def my_in_stock_report(self):
        if request.session.uid:
            user = request.env['res.users'].search([('id', '=', request.session.uid)])
            if user and user.partner_id and user.partner_id.id:
                return request.redirect("/shop/quote_my_report/%s" % user.partner_id.id)

    @http.route(['/shop/quote_my_report/<int:partner_id>'], type='http', auth="public", website=True)
    def quote_my_report(self, partner_id):
        _logger.info('In quote my report')
        partner = request.env['res.partner'].sudo().search([('id', '=', partner_id)])
        _logger.info(partner)
        if partner is not None:
            _logger.info(partner.name)
        request.session['my_in_stock_report_sales_channel'] = True
        if request.session.uid:
            _logger.info('Login successfully')
            user = request.env['res.users'].search([('id', '=', request.session.uid)])
            if user and user.partner_id and user.partner_id.active and user.partner_id.id == partner_id:
                context = {'quote_my_report_partner_id': partner_id}
                try:
                    # user.share is False means internal user
                    if user and user.share is False and user.partner_id and user.partner_id.active is False:
                        return http.request.render('website_sales.quote_my_report', {'active': False, 'product_list': {},
                                                                                     'product_sorted_list': {}})
                    else:
                        request.env['quotation.product.list'].with_context(context).sudo().delete_and_create()
                        product_list, product_sorted_list = request.env['quotation.product.list'].sudo().get_product_list(partner_id)
                        return http.request.render('website_sales.quote_my_report', {'active': True, 'product_list': product_list,
                                                                                    'product_sorted_list': product_sorted_list})
                except Exception as e:
                    _logger.error(e)
            else:
                invalid_url = 'The requested URL is not valid for logged in user.'
                return http.request.render('website_sales.quote_my_report', {'invalid_url': invalid_url})
        else:
            portal_url = partner.with_context(signup_force_type_in_url='', lang=partner.lang)._get_signup_url_for_action()[partner.id]
            if portal_url:
                return request.redirect(portal_url+'&redirect=/shop/quote_my_report/%s' % partner.id)
            else:
                return request.redirect('/')

    @http.route(['/add/product/cart'], type='http', auth="public", methods=['POST'], website=True, csrf=False)
    def add_product_in_cart(self):
        _logger.info('In add_product_in_cart')
        user = request.env['res.users'].search([('id', '=', request.session.uid)])
        try:
            product_list, product_list_sorted = request.env['quotation.product.list'].sudo().get_product_list(user.partner_id.id)
            _logger.info('Length of product list : %s', str(len(product_list)))

            if len(product_list) > 0:
                for product_id in product_list:
                    if product_list.get(product_id)['quantity'] > 0 and product_list.get(product_id)['select']:
                        _logger.info('Product added to cart : %s', str(product_list.get(product_id)['product'].id))
                        _logger.info('Product quantity to cart : %s', str(product_list.get(product_id)['quantity']))
                        self.cart_update_custom(product_list.get(product_id)['product'].id,
                                            product_list.get(product_id)['quantity'])
                        _logger.info('Above Product Added to cart')
                return request.redirect("/shop/cart?flag=True&partner=%s" % user.partner_id.id)
            else:
                return request.redirect("/shop/cart?flag=True&partner=%s" % user.partner_id.id)
        except Exception as e:
            _logger.info('While adding product in cart exception occurred')
            _logger.error(e)

    def cart_update_custom(self, product_id, add_qty, set_qty=0, **kw):
        """This route is called when adding a product to cart (no options)."""
        sale_order = request.website.sale_get_order(force_create=True)
        crm_team = request.env['crm.team'].sudo().search([('team_type', '=', 'my_in_stock_report')])

        if sale_order.team_id.team_type != "my_in_stock_report":
            msg = "Channel Type : " + str(sale_order.team_id.name) + " -> " + str(crm_team.name)
            sale_order.sudo().message_post(body=msg)
            sale_order.team_id = crm_team.id
            sale_order.original_team_id = crm_team.id

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

    @http.route(['/shop/cart/update'], type='http', auth="public", methods=['POST'], website=True, csrf=False)
    def cart_update(self, product_id, add_qty=1, set_qty=0, **kw):
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

        if 'my_in_stock_report_sales_channel' in request.session and \
                request.session['my_in_stock_report_sales_channel'] and \
                sale_order.team_id.team_type != "my_in_stock_report":
            crm_team = request.env['crm.team'].sudo().search([('team_type', '=', 'my_in_stock_report')])
            msg = "Channel Type : " + str(sale_order.team_id.name) + " -> " + str(crm_team.name)
            sale_order.sudo().message_post(body=msg)
            sale_order.team_id = crm_team.id
            request.session.pop('my_in_stock_report_sales_channel')

        sale_order._cart_update(
            product_id=int(product_id),
            add_qty=add_qty,
            set_qty=set_qty,
            product_custom_attribute_values=product_custom_attribute_values,
            no_variant_attribute_values=no_variant_attribute_values
        )
        return request.redirect("/shop/cart")


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
