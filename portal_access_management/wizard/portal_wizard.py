# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo.tools.translate import _
from odoo.exceptions import UserError

from odoo import api, models


_logger = logging.getLogger(__name__)

# welcome email sent to portal users
# (note that calling '_' has no effect except exporting those strings for translation)


class PortalWizardUser(models.TransientModel):
    """
        A model to configure users in the portal wizard.
    """

    _inherit = 'portal.wizard.user'
    _description = 'Portal User Config'

    def _send_email(self):
        """ send notification email to a new portal user """
        if not self.env.user.email:
            raise UserError(_('You must have an email address in your User Preferences to send emails.'))

        # determine subject and body in the portal user's language
        if self.wizard_id.custom_portal_access:
            template = self.env.ref(
                'portal_access_management.mail_template_data_portal_welcome_portal_access_scheduler')
        else:
            template = self.env.ref('portal_access_management.mail_template_data_portal_welcome_cstm')

        for wizard_line in self:
            lang = wizard_line.user_id.lang
            partner = wizard_line.user_id.partner_id

            portal_url = partner.with_context(signup_force_type_in_url='', lang=lang)._get_signup_url_for_action()[
                partner.id]
            partner.signup_prepare()

            if template:
                email_from = 'info@surgicalproductsolutions.com'
                template.with_context(emailFrom=email_from, dbname=self._cr.dbname, portal_url=portal_url, lang=lang).send_mail(
                    wizard_line.id, force_send=False)
            else:
                _logger.warning("No email template found for sending email to the portal user")

        return True