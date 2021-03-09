# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models

class MailComposeForEngine(models.TransientModel):
    _inherit = 'mail.compose.message'

    @api.multi
    def send_mail(self, auto_commit=False):
        if self.template_id.name == 'Vendor Offer - Send by Email' and self._context.get('default_model') == 'purchase.order' \
                and self._context.get('default_res_id'):
            for record in self:
                template = self.env.ref("vendor_offer.email_template_edi_vendor_offer_done_cstm")
                values = {'notification': True}
                values['attachment_ids'] = [(6, 0, [att.id for att in record.attachment_ids])]
                try:
                    values['subject'] = record.subject
                    values['body_html'] = record.body
                    template_id = template.with_context().sudo().send_mail(self._context.get('default_res_id'), raise_exception=True)
                    self.env['mail.mail'].sudo().browse(template_id).write(values)
                except Exception as exc:
                    print("getting error while sending email- Vendor Offer - Send by Email - Custom")

        elif self._context.get('default_model') == 'sale.order' and self._context.get('default_res_id') and self._context.get('mark_so_as_sent'):
            order = self.env['sale.order'].browse([self._context['default_res_id']])
            print('Team Type : %r', order.team_id.team_type)
            # if order.team_id.team_type == 'engine':
            #     order.with_context(tracking_disable=True).state = 'sent'
            self = self.with_context(mail_post_autofollow=True)
            return super(MailComposeForEngine, self).send_mail(auto_commit=auto_commit)
        else:
            return super(MailComposeForEngine, self).send_mail(auto_commit=auto_commit)
