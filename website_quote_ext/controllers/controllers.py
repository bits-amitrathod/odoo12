# -*- coding: utf-8 -*-
import werkzeug

from odoo import exceptions, fields, http, _
from odoo.http import request
from odoo.tools import consteq
from odoo.addons.portal.controllers.portal import get_records_pager
from odoo.addons.sale.controllers.portal import CustomerPortal
from odoo.addons.portal.controllers.mail import _message_post_helper
from odoo.osv import expression
from odoo.exceptions import AccessError

class WebsiteSale(http.Controller):

    def _order_check_access(self, order_id, access_token=None):
        order = request.env['sale.order'].browse([order_id])
        order_sudo = order.sudo()
        try:
            order.check_access_rights('read')
            order.check_access_rule('read')
        except AccessError:
            if not access_token or not consteq(order_sudo.access_token, access_token):
                raise
        return order_sudo

    def _order_get_page_view_values(self, order, access_token, **kwargs):
        order_invoice_lines = {il.product_id.id: il.invoice_id for il in order.invoice_ids.mapped('invoice_line_ids')}
        values = {
            'order': order,
            'order_invoice_lines': order_invoice_lines,
        }
        if access_token:
            values['no_breadcrumbs'] = True
            values['access_token'] = access_token
        values['portal_confirmation'] = order.get_portal_confirmation_action()

        if kwargs.get('error'):
            values['error'] = kwargs['error']
        if kwargs.get('warning'):
            values['warning'] = kwargs['warning']
        if kwargs.get('success'):
            values['success'] = kwargs['success']

        history = request.session.get('my_orders_history', [])
        values.update(get_records_pager(history, order))

        return values


    @http.route(['/shop/engine/update_json'], type='json', auth="public", methods=['POST'], website=True, csrf=False)
    def cart_update_json(self, quote_id,product_id, line_id=None, add_qty=None, set_qty=None, display=True):
        count = request.website.sale_get_engine_order(quote_id, line_id, set_qty,product_id)
        return count

    @http.route(['/my/orders/edit/<int:order>'], type='http', auth="public", website=True)
    def portal_order_page(self, order=None, access_token=None, **kw):
        try:
            order_sudo = self._order_check_access(order, access_token=access_token)
        except AccessError:
            return request.redirect('/my')
        values = self._order_get_page_view_values(order_sudo, access_token, **kw)
        return request.render("website_quote_ext.portal_order_page_ex", values)
