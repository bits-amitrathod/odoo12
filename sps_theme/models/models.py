# -*- coding: utf-8 -*-
from typing import Dict, Any
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class website_cstm(models.Model):
    _name = 'sps_theme.product_instock_notify'

    email = fields.Char()
    product_tmpl_id = fields.Many2one('product.template', 'Product Template', ondelete='cascade', required=True)
    status = fields.Selection([('pending', 'Pending'),('done', 'Done')])

    @api.model
    def send_email_product_instock(self):
        StockNotifcation = self.env['sps_theme.product_instock_notify'].sudo()
        subcribers = StockNotifcation.search([
            ('status', '=', 'pending'),
        ])
        notificationList = {}
        template = self.env.ref('sps_theme.mail_template_product_instock_notification_email')
        for subcriber in subcribers:
            if subcriber.product_tmpl_id.actual_quantity > 0:
                if not subcriber.email in notificationList :
                    notificationList[subcriber.email] = []
                notificationList[subcriber.email].append(subcriber)
                subcriber.status = 'done'

        for email in notificationList:
            products = notificationList[email]
            local_context = {'email': email,'products': products}
            template.with_context(local_context).send_mail(products[0].product_tmpl_id.id, raise_exception=True)

class PporoductTemplate(models.Model):
    _inherit = "product.template"


    def _default_public_categ_ids(self):
        return self.env['product.public.category'].search([('name', 'like', 'All')], limit=1)

    public_categ_ids = fields.Many2many('product.public.category', string='Website Product Category',
                                        help="The product will be available in each mentioned e-commerce category. Go to"
                                             "Shop > Customize and enable 'E-commerce categories' to view all e-commerce categories.",
                                        default=_default_public_categ_ids)