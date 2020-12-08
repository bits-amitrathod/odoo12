# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models

class MailComposeForEngine(models.TransientModel):
    _inherit = 'mail.compose.message'

    @api.multi
    def send_mail(self, auto_commit=False):
        if self.template_id.name == 'Vendor Offer - Send by Email' and self._context.get('default_model') == 'purchase.order' \
                and self._context.get('default_res_id'):
            for wizard in self:
                if wizard.attachment_ids and wizard.composition_mode != 'mass_mail' and wizard.template_id:
                    new_attachment_ids = []
                    for attachment in wizard.attachment_ids:
                        if attachment in wizard.template_id.attachment_ids:
                            new_attachment_ids.append(
                                attachment.copy({'res_model': 'mail.compose.message', 'res_id': wizard.id}).id)
                        else:
                            new_attachment_ids.append(attachment.id)
                    wizard.write({'attachment_ids': [(6, 0, new_attachment_ids)]})
            local_context = {'vendor_email': self._context.get('vendor_email'), 'acq_mgr': self._context.get('acq_mgr')}
            template = self.env.ref('vendor_offer.email_template_edi_vendor_offer_done').sudo()
            try:
                template.with_context(local_context).send_mail(self._context.get('default_res_id'), force_send=True,
                                                               raise_exception=True)
            except Exception as exc:
                print("getting error while sending email")
        elif self._context.get('default_model') == 'sale.order' and self._context.get('default_res_id') and self._context.get('mark_so_as_sent'):
            order = self.env['sale.order'].browse([self._context['default_res_id']])
            print('Team Type : %r', order.team_id.team_type)
            # if order.team_id.team_type == 'engine':
            #     order.with_context(tracking_disable=True).state = 'sent'
            self = self.with_context(mail_post_autofollow=True)
            return super(MailComposeForEngine, self).send_mail(auto_commit=auto_commit)
        else:
            return super(MailComposeForEngine, self).send_mail(auto_commit=auto_commit)
