import json
import logging
# from datetime import datetime
# from werkzeug.exceptions import Forbidden, NotFound
# from werkzeug.urls import url_decode, url_encode, url_parse
from odoo import fields, http, SUPERUSER_ID, tools, _
# from odoo.fields import Command
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale

_logger = logging.getLogger(__name__)

class WebsiteSales(WebsiteSale):


    def fetch_lot_expirydates(self, product_id):
        request.env.cr.execute(
            """SELECT
                sum(quantity), min(use_date), max(use_date)
            FROM
                stock_quant
            INNER JOIN
                stock_lot
            ON
                (
                    stock_quant.lot_id = stock_lot.id)
            INNER JOIN
                stock_location
            ON
                (
                    stock_quant.location_id = stock_location.id)
            WHERE
                stock_location.usage in('internal', 'transit') and stock_lot.product_id = %s """,
            (product_id,))
        return request.env.cr.dictfetchone()

    @http.route(['/shop/capital-equipment','/shop/featured'], type='http', auth="public", website=True, sitemap=WebsiteSale.sitemap_shop)
    def shop_capital_equipment(self,**post):
        result = request.env['product.public.category']
        if request.httprequest.path == "/shop/capital-equipment":
            result = request.env['product.public.category'].search([('name', 'ilike', 'surgical equipment')], limit=1)
        if "featured" in request.httprequest.path:
            result = request.env['product.public.category'].search([('name', 'ilike', 'Featured Products')], limit=1)
        category =  result and result.id
        if category:
            return request.redirect(f'/shop/category/{category}')
        else:
            return request.redirect(f'/shop')


    @http.route([
        '/shop',
        '/shop/page/<int:page>',
        '/shop/category/<model("product.public.category"):category>',
        '/shop/category/<model("product.public.category"):category>/page/<int:page>',
        '/shop/brand/<model("product.brand"):brand>',
        '/shop/brand/<model("product.brand"):brand>/page/<int:page>'
        ], type='http', auth="public", website=True, sitemap=WebsiteSale.sitemap_shop)
    def shop(self, page=0, category=None, search='', min_price=0.0, max_price=0.0, ppg=False, brand=None, **post):
        title = "Shop Surgical Surplus"
        sub_title = "Browse Discount Surgical Surplus in our Online Store"
        if not 'order' in post:
            post.update({'order': 'actual_quantity desc'})

        if brand and not category:
            parent_category = request.env['product.public.category'].sudo().search([('name', '=', 'Manufacturer')])
            category = request.env['product.public.category'].sudo().search([('name', '=', brand.name),('parent_id', '=', parent_category.id)])

        response = super(WebsiteSales,self).shop(page=page, category=category, search=search, min_price=min_price, max_price=max_price, ppg=ppg, **post)

        payload = response.qcontext
        c_all_id = request.env['product.public.category'].search([('name', 'ilike', 'All')], limit=1)
        product_brands = request.env['product.brand']

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

        irConfig = request.env['ir.config_parameter'].sudo()
        payload['isVisibleWebsiteExpirationDate'] = irConfig.get_param('website_sales.website_expiration_date')
        if payload['products'] and payload['isVisibleWebsiteExpirationDate']:
            productProduct = request.env['product.product'].search([('product_tmpl_id', 'in', payload['products'].ids)])
            productMaxMinDates = {}
            for val in productProduct:
                if (val.actual_quantity) > 0:
                    query_result = self.fetch_lot_expirydates(val.id)
                    str_min_date = query_result['min'].strftime('%m/%d/%Y')
                    str_max_date = query_result['max'].strftime('%m/%d/%Y')
                    if (query_result['max'] - query_result['min']).days > 365:
                        str_max_date = "1 Year+"
                    if ((query_result['min'].date() > fields.Datetime.today().date())
                            and ((query_result['min'].date() - fields.Datetime.today().date()).days > 365)
                            and ((query_result['max'].date() - query_result['min'].date()).days > 365)):
                        str_min_date = "-"
                    productMaxMinDates[val.id] = {"min": fields.Datetime.from_string(query_result['min']),
                                                  "max": fields.Datetime.from_string(query_result['max']),
                                                  "str_min": str_min_date,
                                                  "str_max": str_max_date
                                                  }
                else:
                    productMaxMinDates[val.id] = {
                        "min": None,
                        "max": None,
                        "str_min": None,
                        "str_max": None
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
        # payload['brands'] = product_brands
        # payload['brand_id'] = int(brand) if brand else 0
        # payload['keep'] = keep

        if category and category.name == "surgical equipment":
            title = "Surplus Surgical Equipment"
            sub_title = "Shop Surplus Surgical Equipment"

        payload['title'] = title
        payload['sub_title'] = sub_title
        return request.render("website_sale.products", payload)


    def _prepare_product_values(self, product, category, search, **kwargs):
        payload = super(WebsiteSales,self)._prepare_product_values(product, category, search, **kwargs)
        productMaxMinDates = {}
        if (payload['product'].actual_quantity) > 0 and payload['product'].product_variant_id.id:
            query_result = self.fetch_lot_expirydates(payload['product'].product_variant_id.id)
            str_min_date = query_result['min'].strftime('%m/%d/%Y')
            str_max_date = query_result['max'].strftime('%m/%d/%Y')
            if (query_result['max'] - query_result['min']).days > 365:
                str_max_date = "1 Year+"
            if ((query_result['min'].date() > fields.Datetime.today().date())
                    and ((query_result['min'].date() - fields.Datetime.today().date()).days > 365)
                    and ((query_result['max'].date() - query_result['min'].date()).days > 365)):
                str_min_date = "-"
            productMaxMinDates[payload['product'].product_variant_id.id] = {
                "min": fields.Datetime.from_string(query_result['min']),
                "max": fields.Datetime.from_string(query_result['max']),
                "str_min": str_min_date,
                "str_max": str_max_date
            }
        else:
            productMaxMinDates[payload['product'].product_variant_id.id] = {
                "min": None,
                "max": None,
                "str_min": None,
                "str_max": None
            }

        payload['productExpiration'] = productMaxMinDates
        payload['userEmail'] = request.env.user.email
        payload['isVisibleWebsiteExpirationDate'] = request.env['ir.config_parameter'].sudo().get_param('website_sales.website_expiration_date')

        return payload




    # TODO Need to text and fix below code
    @http.route(['/add/product/cart'], type='http', auth="public", methods=['POST'], website=True, csrf=False)
    def add_product_in_cart(self):
        _logger.info('update_quote_my_report_json_list In add_product_in_cart')
        user = request.env['res.users'].search([('id', '=', request.session.uid)])
        try:
            product_list, product_list_sorted = request.env['quotation.product.list'].sudo().get_product_list(user.partner_id.id)
            _logger.info('update_quote_my_report_json_list Length of product list : %s', str(len(product_list)))

            if len(product_list) > 0:
                for product_id in product_list:
                    if product_list.get(product_id)['quantity'] > 0 and product_list.get(product_id)['select']:
                        _logger.info('update_quote_my_report_json_list Product added to cart : %s', str(product_list.get(product_id)['product'].id))
                        _logger.info('update_quote_my_report_json_list Product quantity to cart : %s', str(product_list.get(product_id)['quantity']))
                        self.cart_update_custom(product_list.get(product_id)['product'].id,
                                            product_list.get(product_id)['quantity'])
                        _logger.info('update_quote_my_report_json_list Above Product Added to cart')
                return request.redirect("/shop/cart?flag=True&partner=%s" % user.partner_id.id)
            else:
                return request.redirect("/shop/cart?flag=True&partner=%s" % user.partner_id.id)
        except Exception as e:
            _logger.info('update_quote_my_report_json_list While adding product in cart exception occurred')
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

    def cart_update(self, product_id, add_qty=1, set_qty=0, **kw):
        """This route is called when adding a product to cart (no options)."""
        sale_order = request.website.sale_get_order(force_create=True)
        if sale_order.state != 'draft':
            request.session['sale_order_id'] = None
            sale_order = request.website.sale_get_order(force_create=True)
        response = super(WebsiteSales,self).cart_update(product_id=product_id, add_qty=add_qty, set_qty=set_qty, **kw)

        # SPS Custom code below ........................................
        if 'my_in_stock_report_sales_channel' in request.session and \
                request.session['my_in_stock_report_sales_channel'] and \
                sale_order.team_id.team_type != "my_in_stock_report":
            crm_team = request.env['crm.team'].sudo().search([('team_type', '=', 'my_in_stock_report')])
            msg = "Channel Type : " + str(sale_order.team_id.name) + " -> " + str(crm_team.name)
            sale_order.sudo().message_post(body=msg)
            sale_order.team_id = crm_team.id
            request.session.pop('my_in_stock_report_sales_channel')

        return response

    def payment_confirmation(self, **post):

        responce = super(WebsiteSales, self).payment_confirmation(**post)

        # SPS Custom code to sent the Quotation email to customer when payment confirms............
        order = responce.qcontext['order']
        order.workflow_process_id = 1
        _logger.info('- sale_order_no: %s', order.name)
        _logger.info('- workflow_id : %s', order.workflow_process_id)
        if order.workflow_process_id:
            _logger.info('- workflow_name : %s', order.workflow_process_id.name)

        template = request.env.ref('website_sales.website_order_placed').sudo()

        if request.env.user.user_id.id and not request.env.user.user_id.id == order.user_id.id:
            order.user_id = request.env.user.user_id
        template.email_from = 'info@surgicalproductsolutions.com'
        template.send_mail(order.id, force_send=False)
        msg = "Quotation Email Sent to: " + order.user_id.login
        order.message_post(body=msg)
        _logger.info('End In payment_confirmation')
        # custom code ends .........................................................................
        return responce



# UPG_ODOO16_NOTE .,..........................................
# TODO below controller usage is still not confirm and we are skipping it for now
class WebsiteSaleOptionsCstm(WebsiteSale):
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
