# controllers/main.py
from pickle import FALSE

from odoo import http
from odoo.http import request
from datetime import date

from odoo.addons.mrp.controller.main import logger


class InStockUnsubscribe(http.Controller):



    # This method is written to load parent company and related contacts to template.
    @http.route('/unsubscribe-instock', type='http', auth='user', website=True)
    def unsubscribe_form(self, **kwargs):
        user_partner = request.env.user.partner_id
        parent_company = user_partner.parent_id or user_partner


        # Get all potential contacts (company and individuals) within the hierarchy
        # that have an email and are not already ended.
        all_potential_contacts = request.env['res.partner'].sudo().search([
            ('id', 'child_of', parent_company.id),
            ('email', '!=', False),
            ('end_date', '=', False),
        ])

        # We create a new list that will only contain one contact per unique email address.
        # This ensures the email is not shown twice on the form.
        display_contacts = []
        seen_emails = set()
        for contact in all_potential_contacts:
            if contact.email and contact.email not in seen_emails:
                display_contacts.append(contact)
                seen_emails.add(contact.email)


        return request.render('sps_theme.instock_unsubscriber_page_template', {
            'contacts': display_contacts,
            # Pass the de-duplicated list to the template
            'company': parent_company,
        })

    # This method get data and set end date and feedback for particular id
    @http.route('/unsubscribe-instock/submit', type='http', auth='user', methods=['POST'], csrf=True, website=True)
    def unsubscribe_submit(self, **post):
        contact_ids_str = request.httprequest.form.getlist('contact_ids')
        feedback = post.get('feedback')

        submitted_contacts = request.env['res.partner'].sudo().browse([int(cid) for cid in contact_ids_str])

        emails_to_unsubscribe = list(set(c.email for c in submitted_contacts if c.email))

        user_partner = request.env.user.partner_id
        parent_company = user_partner.parent_id or user_partner
        contacts_to_update = request.env['res.partner'].sudo().search([
            ('id', 'child_of', parent_company.id),
            ('email', 'in', emails_to_unsubscribe)
        ])

        if contacts_to_update:
            for contact in contacts_to_update:
                contact.write({
                    'end_date': date.today(),
                    'unsubscribe_feedback': feedback
                })

        return request.render('sps_theme.instock_unsubscribe_success')

    # After successful submission of feedback , redirect to thank you page template
    @http.route('/unsubscribe-instock/thank-you', type='http', auth='user', website=True)
    def unsubscribe_thank_you(self):
        return request.render('sps_theme.instock_unsubscribe_success')




