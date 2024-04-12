# -*- coding: utf-8 -*-
import werkzeug
import logging
from collections import OrderedDict
from odoo import fields as odoo_fields, tools, _
from odoo import exceptions, http, _
from odoo.http import request
from odoo.tools import consteq
from odoo.addons.portal.controllers.mail import _message_post_helper
from odoo.osv import expression
from odoo.exceptions import AccessError
from odoo.addons.portal.controllers.portal import get_records_pager, pager as portal_pager, CustomerPortal
from datetime import datetime
from odoo.exceptions import AccessError, MissingError
from odoo.addons.payment.controllers.portal import PaymentProcessing
from odoo.addons.portal.controllers.mail import _message_post_helper
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager, get_records_pager
_logger = logging.getLogger(__name__)
SUPERUSER_ID = 2


_logger = logging.getLogger(__name__)

SUPERUSER_ID = 2


class WebsiteSale(http.Controller):
    def _document_check_access(self, model_name, document_id, access_token=None):
        document = request.env[model_name].browse([document_id])
        document_sudo = document.sudo().exists()
        if not document_sudo:
            raise MissingError(_("This document does not exist."))
        try:
            document.check_access_rights('read')
            document.check_access_rule('read')
        except AccessError:
            if not access_token or not consteq(document_sudo.access_token, access_token):
                raise
        return document_sudo

    def _order_get_page_view_values(self, order, access_token, **kwargs):
        order_invoice_lines = {il.product_id.id: il.invoice_id for il in order.invoice_ids.mapped('invoice_line_ids')}
        values = {
            'order': order,
            'order_invoice_lines': order_invoice_lines,
        }
        if access_token:
            values['no_breadcrumbs'] = True
            values['access_token'] = access_token
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
    def update_engine_json(self, quote_id,product_id, line_id=None, add_qty=None, set_qty=None, display=True):
        count=0
        '''if(set_qty==0):
            #message="Product removed "+ product_id +" by customer"
            #_message_post_helper(message=message, res_id=quote_id, res_model='sale.order')
            count = request.website.sale_order_line_del(quote_id, line_id, product_id)
        else:'''
        count = request.website.sale_get_engine_order(quote_id, line_id, set_qty, product_id)
        return count

    @http.route(['/shop/engine/count'], type='json', auth="public", methods=['POST'], website=True, csrf=False)
    def cart_update_json(self, quote_id,product_id, line_id=None, add_qty=None, set_qty=None, display=True):
        count = request.website.sale_get_engine_count(quote_id,product_id)
        return count

    @http.route(['/my/orders/edit/<int:order_id>'], type='http', auth="public", website=True)
    def portal_order_page_edit(self, order_id, report_type=None, access_token=None, message=False, download=False, **kw):
        print('In portal_order_page')
        try:
            order_sudo = self._document_check_access('sale.order', order_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=order_sudo, report_type=report_type,
                                     report_ref='sale.action_report_saleorder', download=download)

        # use sudo to allow accessing/viewing orders for public user
        # only if he knows the private token
        now = odoo_fields.Date.today()

        # Log only once a day
        if order_sudo and request.session.get(
                'view_quote_%s' % order_sudo.id) != now and request.env.user.share and access_token:
            request.session['view_quote_%s' % order_sudo.id] = now
            body = _('Quotation viewed by customer')
            _message_post_helper(res_model='sale.order', res_id=order_sudo.id, message=body,
                                 token=order_sudo.access_token, message_type='notification', subtype_xmlid="mail.mt_note",
                                 partner_ids=order_sudo.user_id.sudo().partner_id.ids)

        values = {
            'sale_order': order_sudo,
            'message': message,
            'token': access_token,
            'return_url': '/shop/payment/validate',
            'bootstrap_formatting': True,
            'partner_id': order_sudo.partner_id.id,
            'report_type': 'html',
        }
        if order_sudo.company_id:
            values['res_company'] = order_sudo.company_id

        if order_sudo.has_to_be_paid():
            domain = expression.AND([
                [('company_id', '=', order_sudo.company_id.id)], # '&', ('website_published', '=', True),
                [('country_ids', 'in', [order_sudo.partner_id.country_id.id])] #'|', ('specific_countries', '=', False),
            ])
            acquirers = request.env['payment.acquirer'].sudo().search(domain)

            values['acquirers'] = acquirers.filtered(
                lambda acq: (acq.payment_flow == 'form' and acq.view_template_id) or
                            (acq.payment_flow == 's2s' and acq.registration_view_template_id))
            values['pms'] = request.env['payment.token'].search(
                [('partner_id', '=', order_sudo.partner_id.id),
                 ('acquirer_id', 'in', acquirers.filtered(lambda acq: acq.payment_flow == 's2s').ids)])

        if order_sudo.state in ('draft', 'sent', 'cancel'):
            history = request.session.get('my_quotations_history', [])
        else:
            history = request.session.get('my_orders_history', [])
        values.update(get_records_pager(history, order_sudo))

        return request.render("website_quote_ext.portal_order_page_ex", values)

    @http.route('/notifymeclientorderref', type='json', auth="public", methods=['POST'], website=True, csrf=False)
    def notifymeclientorderref(self, client_order_ref, orderId):
        sale_order = request.env['sale.order'].sudo().search([('id', '=', orderId)])
        if not sale_order.x_studio_allow_duplicate_po:
            result = request.env['sale.order'].sudo().search(
                [('client_order_ref', '=', client_order_ref),
                 ('partner_id', 'in', sale_order.get_chils_parent())])
            if result:
                result2 = request.env['sale.order'].sudo().search(
                    [('client_order_ref', '=', client_order_ref),
                     ('partner_id', 'in', sale_order.get_chils_parent()),
                     ('x_studio_allow_duplicate_po', '=', True)
                     ])
                if result2:
                    return {'client_order_ref_error': ''}
                else:
                    return {'client_order_ref_error': 'The PO number is already present on another Sales Order'}
            else:
                return {'client_order_ref_error': ''}

    @http.route(['/my/orders/<int:order_id>/accepts'], type='http', auth="public", methods=['POST'], website=True)
    def accepts(self, order_id, access_token=None, **post):
        try:
            order_sudo = self._document_check_access('sale.order', order_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        message = post.get('accept_message')

        flag = False
        query_string=False
        Order = request.env['sale.order'].sudo().browse(order_id)
        SaleOrderLines = request.env['sale.order.line'].sudo().search([('order_id', '=', Order.id)])
        for SaleOrderLine in SaleOrderLines:
            StockMove = request.env['stock.move'].sudo().search([('sale_line_id', '=', SaleOrderLine.id)])
            if SaleOrderLine.product_uom_qty >= 0 and StockMove.product_uom_qty >= 0:
                if SaleOrderLine.product_uom_qty < StockMove.product_uom_qty:
                    flag = True
                    break

        if access_token != Order.access_token:
            return request.render('website.404')
        if Order.state != 'sent':
            return request.redirect(order_sudo.get_portal_url(query_string=query_string))

        if flag:
            Order.action_cancel()
            Order.action_draft()
            Order.action_confirm()

            # picking = request.env['stock.picking'].sudo().search([('sale_id', '=', Order.id), ('picking_type_id', '=', 1), ('state', 'not in', ['draft', 'cancel'])])
            # picking.write({'state': 'assigned'})
            # stock_move = request.env['stock.move'].sudo().search([('picking_id', '=', picking.id)])
            # stock_move.write({'state': 'assigned'})
        else:
            Order.write({'state': 'sale'})  # , 'confirmation_date': datetime.now()

        client_order_ref = post.get('client_order_ref')
        if client_order_ref:
            Order.write({"client_order_ref": client_order_ref})
        if message:
            Order.write({'sale_note': message})
            body = _(message)
            _message_post_helper(res_model='sale.order', res_id=order_id, message=body, token=access_token,
                                 message_type='notification', subtype_xmlid="mail.mt_note",
                                 partner_ids=Order.user_id.sudo().partner_id.ids)
            # stock picking notification
            stock_picking = request.env['stock.picking'].sudo().search([('sale_id', '=', order_id)])
            stock_picking_sudo = stock_picking.sudo()

            for stk_picking in stock_picking_sudo:
                values = {
                    'body': body,
                    'model': 'stock.picking',
                    'message_type': 'notification',
                    'no_auto_thread': False,
                    'subtype_id': request.env['ir.model.data']._xmlid_to_res_id('mail.mt_note', raise_if_not_found=True),
                    'res_id': stk_picking.id,
                    'author_id': stk_picking.sale_id.partner_id.id,
                }
                request.env['mail.message'].sudo().create(values)

        # Send email to Salesperson and Admin when sales order accepted(Confirm)
        upload_type = None
        salesperson_email = None
        key_account_email = ''
        if Order.order_line[0].customer_request_id and Order.order_line[0].customer_request_id.document_id and Order.order_line[0].customer_request_id.document_id.source:
            upload_type = Order.order_line[0].customer_request_id.document_id.source
        if Order.user_id and Order.user_id.partner_id and Order.user_id.partner_id.email:
            salesperson_email = Order.user_id.partner_id.email
        elif Order.partner_id and Order.partner_id.parent_id and Order.partner_id.parent_id.user_id \
                and Order.partner_id.parent_id.user_id.partner_id and Order.partner_id.parent_id.user_id.partner_id.email:
            salesperson_email = Order.partner_id.parent_id.user_id.partner_id.email
        if Order.account_manager and Order.account_manager.partner_id and Order.account_manager.partner_id.email:
            key_account_email = Order.account_manager.partner_id.email
        self._send_sales_order_accepted_email(Order.partner_id.display_name, Order.name, Order.state, salesperson_email, upload_type, message, key_account_email)
        return request.redirect(order_sudo.get_portal_url(query_string=query_string))

    @staticmethod
    def _send_sales_order_accepted_email(customer_name, sales_order_name, sales_order_status, salespersonEmail, upload_type, note, key_account_email):
        today_date = datetime.today().strftime('%m/%d/%Y')
        template = request.env.ref('website_quote_ext.stockhawk_sales_order_confirm_email_response').sudo()
        local_context = {'customer_name': customer_name, 'sales_order_name': sales_order_name,'salesperson_email': salespersonEmail,
                         'date': today_date, 'sales_order_status': sales_order_status, 'upload_type': upload_type, 'note': note,
                         'key_account_email': key_account_email}
        try:
            template.with_context(local_context).send_mail(SUPERUSER_ID, raise_exception=True)
        except Exception as exc:
            _logger.error("getting error while sending email of sales order : %r", exc)
            response = {'message': 'Unable to connect to SMTP Server'}

    @http.route(['/my/orders/<int:order_id>/declines'], type='http', auth="public", methods=['POST'], website=True)
    def decline(self, order_id, access_token=None, **post):
        try:
            order_sudo = self._document_check_access('sale.order', order_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        order_sudo.action_cancel()
        message = post.get('decline_message')

        if message:
            order_sudo.write({'sale_note': message})
            body = _(message)
            _message_post_helper(res_model='sale.order', res_id=order_id, message=body, token=access_token,
                                 message_type='notification', subtype_xmlid="mail.mt_note",
                                 partner_ids=order_sudo.user_id.sudo().partner_id.ids)

            # stock picking notification
            stock_picking = request.env['stock.picking'].sudo().search([('sale_id', '=', order_id)])
            stock_picking_sudo = stock_picking.sudo()

            for stk_picking in stock_picking_sudo:
                values = {
                    'body': body,
                    'model': 'stock.picking',
                    'message_type': 'notification',
                    'no_auto_thread': False,
                    'subtype_id': request.env['ir.model.data']._xmlid_to_res_id('mail.mt_note', raise_if_not_found=True),
                    'res_id': stk_picking.id,
                    'author_id': stk_picking.sale_id.partner_id.id,
                }
                request.env['mail.message'].sudo().create(values)

        query_string = False

        return request.redirect(order_sudo.get_portal_url(query_string=query_string))


class CustomerPortal(CustomerPortal):

    def _prepare_portal_layout_values(self):
        # get customer sales rep
        values = super(CustomerPortal, self)._prepare_portal_layout_values()
        PuchaseOrder = request.env['purchase.order']
        sales_user = False
        partner = request.env.user.partner_id
        vendor_count = PuchaseOrder.search_count([
            ('message_partner_ids', 'child_of', [partner.commercial_partner_id.id]),
            ('state', 'in', ['ven_sent', 'cancel'])
        ])

        if partner.account_manager_cust and not partner.account_manager_cust._is_public():
            sales_user = partner.account_manager_cust
        elif partner.user_id and not partner.user_id._is_public():
            if partner.user_id.partner_id.name == "National Accounts":
                if partner.national_account_rep and not partner.national_account_rep._is_public():
                    sales_user = partner.national_account_rep
                else:
                    sales_user = partner.user_id
            else:
                sales_user = partner.user_id

        values.update({
            'sales_user': sales_user,
            'page_name': 'home',
            'archive_groups': [],
            'vendor_count':vendor_count,
        })
        return values

    def _get_archive_groups(self, model, domain=None, fields=None, groupby="create_date", order="create_date desc"):
        if not model:
            return []
        if domain is None:
            domain = []
        if fields is None:
            fields = ['name', 'create_date']
        groups = []
        for group in request.env[model]._read_group_raw(domain, fields=fields, groupby=groupby, orderby=order):
            dates, label = group[groupby]
            date_begin, date_end = dates.split('/')
            groups.append({
                'date_begin': odoo_fields.Date.to_string(odoo_fields.Date.from_string(date_begin)),
                'date_end': odoo_fields.Date.to_string(odoo_fields.Date.from_string(date_end)),
                'name': label,
                'item_count': group[groupby + '_count']
            })
        return groups

    @http.route(['/my/vendor', '/my/vendor/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_vendor_offers(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        PurchaseOrder = request.env['purchase.order']

        domain = [
            '|',
            ('message_partner_ids', 'child_of', [partner.commercial_partner_id.id]),
            ('partner_id', 'child_of', [partner.commercial_partner_id.id]),
        ]

        archive_groups = self._get_archive_groups('purchase.order', domain)
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'create_date desc, id desc'},
            'name': {'label': _('Name'), 'order': 'name asc, id asc'},
            'amount_total': {'label': _('Total'), 'order': 'amount_total desc, id desc'},
        }
        # default sort by value
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        searchbar_filters = {
            'all': {'label': _('All'), 'domain': [('state', 'in', ['ven_sent', 'done', 'cancel'])]},
            'vendor offer': {'label': _('Vendor Offer'), 'domain': [('state', '=', 'ven_sent')]},
            'cancel': {'label': _('Cancelled'), 'domain': [('state', '=', 'cancel')]},
        }
        # default filter by value
        if not filterby:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']

        # count for pager
        vendor_count = PurchaseOrder.search_count(domain)
        # make pager
        pager = portal_pager(
            url="/my/vendor",
            url_args={'date_begin': date_begin, 'date_end': date_end},
            total=vendor_count,
            page=page,
            step=self._items_per_page
        )
        # search the purchase orders to display, according to the pager data
        orders = PurchaseOrder.search(
            domain,
            order=order,
            limit=self._items_per_page,
            offset=pager['offset']
        )
        request.session['my_purchases_history'] = orders.ids[:100]

        values.update({
            'date': date_begin,
            'orders': orders,
            'page_name': 'Vendor Offer',
            'pager': pager,
            'archive_groups': archive_groups,
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
            'default_url': '/my/vendor',
        })
        return request.render("website_quote_ext.portal_my_vendor_offers", values)

    @http.route(['/my/vendor/<int:order_id>'], type='http', auth="public", website=True)
    def portal_my_vendor_offer(self, order_id=None, **kw):
        order = request.env['purchase.order'].browse(order_id)
        try:
            order.check_access_rights('read')
            order.check_access_rule('read')
        except AccessError:
            return request.redirect('/my')
        #history = request.session.get('my_purchases_history', [])
        values = {
            'order': order.sudo(),
        }
        #values.update(get_records_pager(history, order))
        if order.state == 'purchase':
            return request.redirect('/my')
        else:
            return request.render("website_quote_ext.portal_my_vendor_offer", values)

    @http.route(['/my/orders/<int:order_id>'], type='http', auth="public", website=True)
    def portal_order_page(self, order_id, report_type=None, access_token=None, message=False, download=False, **kw):
        try:
            order_sudo = self._document_check_access('sale.order', order_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=order_sudo, report_type=report_type,
                                     report_ref='sale.action_report_saleorder', download=download)

        # use sudo to allow accessing/viewing orders for public user
        # only if he knows the private token
        # Log only once a day
        # if order_sudo:
        #     # store the date as a string in the session to allow serialization
        #     now = odoo_fields.Date.today().isoformat()
        #     session_obj_date = request.session.get('view_quote_%s' % order_sudo.id)
        #     if session_obj_date != now and request.env.user.share and access_token:
        #         request.session['view_quote_%s' % order_sudo.id] = now
        #         body = _('Quotation viewed by customer %s', order_sudo.partner_id.name)
        #         _message_post_helper(
        #             "sale.order",
        #             order_sudo.id,
        #             body,
        #             token=order_sudo.access_token,
        #             message_type="notification",
        #             subtype_xmlid="mail.mt_note",
        #             partner_ids=order_sudo.user_id.sudo().partner_id.ids,
        #         )

        values = self._order_get_page_view_values(order_sudo, access_token, **kw)
        values['message'] = message

        return request.render('sale.sale_order_portal_template', values)

    @http.route(['/my/invoices/<int:invoice_id>'], type='http', auth="public", website=True)
    def portal_my_invoice_detail(self, invoice_id, access_token=None, report_type=None, download=False, **kw):
        try:
            invoice_sudo = self._document_check_access('account.move', invoice_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=invoice_sudo, report_type=report_type, report_ref='account.account_invoices',
                                     download=download)

        values = self._invoice_get_page_view_values(invoice_sudo, access_token, **kw)
        pay_ids = []
        for item in values['acquirers']:
            if item.display_name != 'Purchase Order':
                pay_ids.append(item.id)
        acquirers = request.env['payment.acquirer'].search([('id', 'in', pay_ids)])
        values['acquirers'] = acquirers
        #acquirers = values.get('acquirers')

        if acquirers:
            country_id = values.get('partner_id') and values.get('partner_id')[0].country_id.id
            values['acq_extra_fees'] = acquirers.get_acquirer_extra_fees(invoice_sudo.amount_residual,
                                                                         invoice_sudo.currency_id, country_id)

        pay_link = request.env['sale.pay.link.cust'].search([('invoice_id', '=', invoice_id)])
        if pay_link:
            pay_link.allow_pay_gen_payment_link = True
            request.session['payment_link_invoice_id'] = invoice_id
        else:
            log_id = request.env['sale.pay.link.cust'].create({
                'invoice_id': invoice_id,
                'allow_pay_gen_payment_link': True
            })
            request.session['payment_link_invoice_id'] = invoice_id

        return request.render("account.portal_invoice_page", values)
