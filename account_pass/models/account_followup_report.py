from odoo import models, api, _
from odoo.exceptions import UserError
from odoo import models, api, _ ,fields

import logging

# Create a logger
_logger = logging.getLogger(__name__)

class AccountFollowupReport(models.AbstractModel):
    _inherit = "account.followup.report"


    @api.model
    def _send_email(self, options):
        """
        Send follow-up email to customers without logging emails in chatter.
        """
        partner = self.env['res.partner'].browse(options.get('partner_id'))
        followup_contacts = partner._get_all_followup_contacts() or partner
        followup_recipients = options.get('email_recipient_ids', followup_contacts)
        sent_at_least_once = False

        for to_send_partner in followup_recipients:
            email = to_send_partner.email
            if email and email.strip():
                self = self.with_context(lang=partner.lang or self.env.user.lang)

                # Get email body and attachments
                report_html = self.with_context(mail=True).get_followup_report_html(options)

                # Set the responsible person as the sender
                responsible = partner._get_followup_responsible()
                # email_from = responsible.partner_id.email or self.env.user.email
                author_id = responsible.partner_id.id

                # Define fixed email address
                fixed_email = "accounting@shopsps.com"

                # Create a temporary 'mail.message' object for rendering
                message = self.env['mail.message'].sudo().create({
                    'subject': self._get_email_subject(options),
                    'body': report_html,
                    'message_type': 'notification',
                    'record_name': partner.name,
                })

                # Render the `mail_notification_light` template
                rendered_body = self.env['ir.qweb']._render(
                    'mail.mail_notification_light',
                    {
                        'body': report_html,
                        'record': partner,
                        'email_layout': True,
                        'message': message,  # Pass the 'mail.message' object
                        'company': self.env.company,  # Add company to the context
                        'model_description' : _('payment reminder'),
                        'subtype_id' : self.env.ref('mail.mt_note').id,
                    }
                )

                # attachments
                attachment_ids = options.get(
                    'attachment_ids',
                    partner._get_invoices_to_print(options).message_main_attachment_id.ids
                )


                # Create the email
                mail = self.env['mail.mail'].sudo().create({
                    'author_id': author_id,
                    'subject': self._get_email_subject(options),
                    'body_html': rendered_body,
                    'email_from': fixed_email,
                    'reply_to': fixed_email,
                    'attachment_ids': [(6, 0, attachment_ids)],
                    'recipient_ids': [(6, 0, [partner.id for partner in followup_recipients])],

                })

                # Prevent chatter logs for this email
                mail = mail.with_context()
                mail.send()  # Send the email directly

                sent_at_least_once = True

        if not sent_at_least_once:
            raise UserError(
                _("No follow-up contact has an email address set for customer '%s'") % partner.name
            )

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"


    is_user_changed = fields.Boolean(string="Manual Exclusion", compute="_compute_manual_exclusion", inverse="_set_manual_exclusion", store=True)


    def _set_manual_exclusion(self):
        for record in self:
            record.blocked = record.is_user_changed

    @api.depends('blocked', 'date_maturity')
    def _compute_manual_exclusion(self):
        today = fields.Date.context_today(self)
        for record in self:
            previous_due = record._origin.date_maturity
            current_due = record.date_maturity  # Current due date
            # Ensure `blocked` follows `manual_exclusion`, but allow manual changes
            if record.is_user_changed != record.blocked:
                record.blocked = record.is_user_changed

            if record.date_maturity and record.date_maturity <= today:
                record.is_user_changed = False

            else:
                # If the invoice was never manually modified, set exclusion based on blocked status
                if record._origin.is_user_changed is False or record.is_user_changed is False:
                    record.blocked = record.is_user_changed

                # Detect if an invoice was previously overdue and is now non-overdue
                if previous_due and previous_due <= today < current_due:
                    record.is_user_changed = True  # Reset to exclude non-overdue invoices

