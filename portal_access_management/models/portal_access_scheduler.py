
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



class ResPartner(models.Model):
    _inherit = 'res.partner'
    portal_access_email_sent = fields.Boolean('Portal Access Email Sent', default=False)


class PortalAccessScheduler(models.TransientModel):
    _name = 'portal.access.scheduler'
    _description = "PortalAccessScheduler"

    @api.model
    def portal_access_scheduler(self):
        _logger.info('In portal_access_scheduler')
        self.env['portal.wizard'].sudo().get_all_partners()


class PortalUserCustom(models.TransientModel):
    _inherit = 'portal.wizard'

    custom_portal_access = fields.Boolean('Portal Access for purchasing platform', default=False)

    # TODO....
    # ('customer', '=', True), customer column is not found error was showing so we removed that domain from below search query
    def get_all_partners(self):
        today_start = date.today()
        customers = self.env['res.partner'].search(
            [('is_parent', '=', True), ('email', '!=', ''), ('active', '=', True),
             ('portal_access_email_sent', '!=', True),
             '|', '|', '|', '|', '|', '|', ('monday', '=', True), ('tuesday', '=', True), ('wednesday', '=', True),
             ('thursday', '=', True), ('friday', '=', True), ('saturday', '=', True), ('sunday', '=', True)],
            order='id asc', limit=100)

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
                or (customer.end_date != False and self.string_to_date(customer.end_date) >= today_start) \
                or (customer.start_date != False and self.string_to_date(customer.start_date) <= today_start) \
                or (customer.start_date != False and customer.end_date != False and self.string_to_date(customer.start_date) <= today_start and self.string_to_date(customer.end_date) >= today_start) \
                or (customer.end_date is None):

                contacts = self.env['res.partner'].search([('parent_id', '=', customer.id), ('email', '!=', ''), ('active', '=', True)])
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
                        is_portal = contact.user_ids and contact.user_ids[0].has_group('base.group_portal')
                        if not is_portal:
                            error_msg = self.get_error_message(contact)
                            if not error_msg:
                                is_portal = True
                                user_changes.append((0, 0, {
                                    'partner_id': contact.id,
                                    'email': contact.email,
                                    'is_portal': is_portal,
                                    # 'user_id': SUPERUSER_ID,
                                }))

                if user_changes:
                    self.with_env(self.env(user=SUPERUSER_ID)).create({'user_ids': user_changes})
                    records = self.env['portal.wizard'].search([], order="id desc", limit=1)
                    try:
                        records.custom_portal_access = True
                        records.user_ids.action_grant_access()
                    except Exception as e:
                        _logger.error("%s", e)

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
    
    




