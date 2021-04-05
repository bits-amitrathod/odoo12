
import logging
from odoo import api, fields, models
from odoo.tools.translate import _
from odoo.tools import email_split
from datetime import date, datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import time

SUPERUSER_ID = 2

_logger = logging.getLogger(__name__)


def extract_email(email):
    """ extract the email address from a user-friendly email address """
    addresses = email_split(email)
    return addresses[0] if addresses else ''


class PortalAccessScheduler(models.TransientModel):
    _name = 'portal.access.scheduler'

    @api.model
    @api.multi
    def portal_access_scheduler(self):
        _logger.info('In portal_access_scheduler')
        self.env['portal.wizard'].sudo().get_all_partners()


class PortalUserCustom(models.TransientModel):
    _inherit = 'portal.wizard'

    custom_portal_access = fields.Boolean('Portal Access for purchasing platform', default=False)

    @api.multi
    def get_all_partners(self):
        today_date = date.today()
        today_start = today_date
        customers = self.env['res.partner'].search(
            [('customer', '=', True), ('is_parent', '=', True), ('email', '!=', ''), ('active', '=', True),
             '|', '|', '|', '|', '|', '|', ('monday', '=', True), ('tuesday', '=', True), ('wednesday', '=', True),
             ('thursday', '=', True), ('friday', '=', True), ('saturday', '=', True), ('sunday', '=', True)],
            order='id asc', limit=10)


        # ('portal_access_email_sent', '!=', True)

        contacts_ids = []
        contact_ids = set()
        user_changes = []
        email_list_cc = []
        for customer in customers:
            contacts_ids.clear()
            contact_ids.clear()
            user_changes.clear()
            email_list_cc.clear()
            if (customer.start_date == False and customer.end_date == False) \
                    or (customer.end_date != False and self.string_to_date(
                customer.end_date) >= today_start) \
                    or (customer.start_date != False and self.string_to_date(
                customer.start_date) <= today_start) \
                    or (
                    customer.start_date != False and customer.end_date != False and self.string_to_date(
                customer.start_date) <= today_start and self.string_to_date(
                customer.end_date) >= today_start) \
                    or (customer.end_date is None):
                contacts = self.env['res.partner'].search(
                    [('parent_id', '=', customer.id), ('email', '!=', ''), ('active', '=', True)])

                for contact in contacts:
                    if (contact.email != customer.email and contact.email not in email_list_cc):
                        if (contact.start_date == False and contact.end_date == False) \
                                or (contact.start_date == False and self.string_to_date(
                            contact.end_date) and self.string_to_date(
                            contact.end_date) >= today_start) \
                                or (contact.end_date == False and self.string_to_date(
                            contact.start_date) and self.string_to_date(
                            contact.start_date) <= today_start) \
                                or (self.string_to_date(
                            contact.start_date) and self.string_to_date(
                            contact.start_date) <= today_start and self.string_to_date(
                            contact.end_date) and self.string_to_date(
                            contact.end_date) >= today_start):
                            contacts_ids.append(contact.id)
                            email_list_cc.append(contact.email)

                filtered_contacts = self.env['res.partner'].search([('id', 'in', contacts_ids)])
                customer.portal_access_email_sent = True

                contact_partners = filtered_contacts | customer
                for contact in contact_partners:
                    # make sure that each contact appears at most once in the list
                    if contact.id not in contact_ids:
                        contact_ids.add(contact.id)
                        in_portal = False
                        if contact.user_ids:
                            in_portal = self.env.ref('base.group_portal') in contact.user_ids[0].groups_id
                        if in_portal is False:
                            error_msg = self.get_error_message(contact)
                            if not error_msg:
                                in_portal = True
                                user_changes.append((0, 0, {
                                    'partner_id': contact.id,
                                    'email': contact.email,
                                    'in_portal': in_portal,
                                    # 'user_id': SUPERUSER_ID,
                                }))

                if user_changes:
                    self.with_env(self.env(user=SUPERUSER_ID)).create({'user_ids': user_changes})
                    records = self.env['portal.wizard'].search([], order="id desc", limit=1)
                    try:
                        records.custom_portal_access = True
                        records.user_ids.action_apply()
                    except Exception as e:
                        _logger.error("%s", e)

    @api.multi
    def get_error_message(self, partner_id):
        emails = []
        partners_error_empty = self.env['res.partner']
        partners_error_emails = self.env['res.partner']
        partners_error_user = self.env['res.partner']
        partners_error_internal_user = self.env['res.partner']

        if partner_id:
            email = extract_email(partner_id.email)
            if not email:
                partners_error_empty |= partner_id
            elif email in emails:
                partners_error_emails |= partner_id
            user = self.env['res.users'].sudo().with_context(active_test=False).search([('login', '=ilike', email)])
            if user:
                partners_error_user |= partner_id
                emails.append(email)

        if partner_id:
            if any(u.has_group('base.group_user') for u in partner_id.user_ids):
                partners_error_internal_user |= partner_id

        error_msg = []
        if partners_error_empty:
            error_msg.append("%s\n- %s" % (_("Some contacts don't have a valid email: "),
                                           '\n- '.join(partners_error_empty.mapped('display_name'))))
        if partners_error_emails:
            error_msg.append("%s\n- %s" % (_("Several contacts have the same email: "),
                                           '\n- '.join(partners_error_emails.mapped('email'))))
        if partners_error_user:
            error_msg.append("%s\n- %s" % (_("Some contacts have the same email as an existing portal user:"),
                                           '\n- '.join(
                                               ['%s <%s>' % (p.display_name, p.email) for p in partners_error_user])))
        if partners_error_internal_user:
            error_msg.append("%s\n- %s" % (_("Some contacts are already internal users:"),
                                           '\n- '.join(partners_error_internal_user.mapped('email'))))
        if error_msg:
            error_msg.append(_("To resolve this error, you can: \n"
                               "- Correct the emails of the relevant contacts\n"
                               "- Grant access only to contacts with unique emails"))
            error_msg[-1] += _("\n- Switch the internal users to portal manually")
        return error_msg

    @staticmethod
    def string_to_date(date_string):
        if date_string == False:
            return None
        datestring = str(date_string)
        return datetime.strptime(str(datestring), DEFAULT_SERVER_DATE_FORMAT).date()
    
    
class ResPartner(models.Model):
    _inherit = 'res.partner'

    portal_access_email_sent = fields.Boolean('Portal Access Email Sent', default=False)





