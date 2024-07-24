# -*- coding: utf-8 -*-

import logging
from odoo import fields, http
from odoo.http import request

_logger = logging.getLogger(__name__)

class WebsiteSalesReports(http.Controller):

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
        # _logger.info(' update_quote_my_report_json_list -----------------------------')
        # _logger.info('- update_quote_my_report_json_list  partner_id id : %s', partner_id)
        # _logger.info('- update_quote_my_report_json_list  product_id id : %s', product_id)
        # _logger.info('- update_quote_my_report_json_list  new_qty id : %s', new_qty)
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

