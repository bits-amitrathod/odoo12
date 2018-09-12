# -*- coding: utf-8 -*-

from odoo import models, fields, api

class website_cstm(models.Model):
    _name = 'website_cstm.product_instock_notify'

    email = fields.Char()
    product_tmpl_id = fields.Many2one('product.template', 'Product Template', ondelete='cascade', required=True)
    status = fields.Selection([('pending', 'Pending'),('done', 'Done')])

    @api.model
    def send_email_product_instock(self):
        StockNotifcation = self.env['website_cstm.product_instock_notify'].sudo()
        subcribers = StockNotifcation.search([
            ('status', '=', 'pending'),
        ])

        template = self.env.ref('website_cstm.mail_template_product_instock_notification_email')
        for subcriber in subcribers:
            if subcribers.product_tmpl_id.qty_available > 0:
                local_context = {'email': subcriber.email}
                template.with_context(local_context).send_mail(subcriber.product_tmpl_id.id, raise_exception=True)
                subcriber.status='done'