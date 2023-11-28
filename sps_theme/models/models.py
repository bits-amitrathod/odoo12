# -*- coding: utf-8 -*-
from typing import Dict, Any
from odoo import models, fields, api
from odoo.tools.translate import _
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

class SaleOrder1(models.Model):
    _inherit = 'sale.order'
    def _cart_lines_stock_update(self, values, **kwargs):
        line_id = values.get('line_id')
        for line in self.order_line:
            if line.product_id.type == 'product' and line.product_id.inventory_availability in ['always', 'threshold']:
                cart_qty = sum(self.order_line.filtered(lambda p: p.product_id.id == line.product_id.id).mapped('product_uom_qty'))
                if (line_id == line.id) and cart_qty > line.product_id.actual_quantity:
                    qty = line.product_id.with_context(warehouse=self.warehouse_id.id).actual_quantity - cart_qty
                    new_val = self._cart_update(line.product_id.id, line.id, qty, 0, **kwargs)
                    # new_val['quantity'] = line.product_id.actual_quantity
                    values.update(new_val)

                    # Make sure line still exists, it may have been deleted in super()_cartupdate because qty can be <= 0
                    if line.exists() and new_val['quantity']:
                        line.warning_stock = _('You ask for %s products but only %s is available') % (cart_qty, new_val['quantity'])
                        values['warning'] = line.warning_stock
                    else:
                        self.warning_stock = _("Some products became unavailable and your cart has been updated. We're sorry for the inconvenience.")
                        values['warning'] = self.warning_stock
        return values

    def check_product_qty_before_sale(self):
        val =[]
        for lines in self.order_line:
            warning = lines._onchange_product_id_check_availability()
            if warning :
                val.append(warning)
        flag = True if len(val) > 0 else False
        return flag

