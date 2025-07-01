# controllers/main.py
from pickle import FALSE

from odoo import http , fields
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
        # Those have an email.
        # In-stock email notification checkboxes are not set true.
        all_potential_contacts = request.env['res.partner'].sudo().search([
            ('id', 'child_of', parent_company.id),
            ('type','=','contact'),
            ('email', '!=', False),
            ('instock_unsubscribe','=', False) ,
            ('disable_all_instock_email', '=', False)
        ])

        if parent_company.email and not parent_company.instock_unsubscribe and not parent_company.disable_all_instock_email:
            all_potential_contacts  |= parent_company  # add to recordset

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
        user_partner = request.env.user.partner_id
        parent_company = user_partner.parent_id or user_partner
        feedback = post.get('feedback')
        submitted_contacts = request.env['res.partner'].sudo().browse([int(cid) for cid in contact_ids_str])

        emails_to_unsubscribe = list(set(c.email for c in submitted_contacts if c.email))

        related_contacts = request.env['res.partner'].sudo().search([
            ('id', 'child_of', parent_company.id)
        ])

        # contacts_to_update = request.env['res.partner'].sudo().search([
        #     ('id', 'child_of', parent_company.id),
        #     # ('email', 'in', emails_to_unsubscribe)
        # ])

        unsubscribe_all = post.get('unsubscribe_all') == 'on'

        if unsubscribe_all:
            # Set global unsubscribe at company level
            parent_company.sudo().write({'disable_all_instock_email': True})

            # Set feedback for all contacts
            for contact in related_contacts:
                contact.sudo().write({
                    'instock_unsubscribe': True,
                    'unsubscribe_feedback': feedback,
                    'unsubscribe_date': fields.Datetime.now()
                })

        else:
            # Ensure company-wide opt-out is OFF
            parent_company.sudo().write({'disable_all_instock_email': False})

            for contact in submitted_contacts:

                is_checked = str(contact.id) in contact_ids_str
                logger.info('is_checked %s', is_checked)

                contact.sudo().write({
                    'instock_unsubscribe': is_checked,
                    'unsubscribe_feedback': feedback,
                    'unsubscribe_date': fields.Datetime.now()

                })

                # NEW: Also update parent company if email is same and checkbox was checked
                if is_checked and contact.email and contact.email == parent_company.email:
                    # Find all contacts with the same email (includes parent if it shares the email)
                    all_same_email = request.env['res.partner'].sudo().search([
                        ('email', '=', contact.email),
                        ('id', 'in', related_contacts.ids)
                    ])

                    for record in all_same_email:
                        logger.info('record %s', record)
                        record.sudo().write({
                            'instock_unsubscribe': True,
                            'unsubscribe_feedback': feedback,
                            'unsubscribe_date': fields.Datetime.now()
                        })


        return request.render('sps_theme.instock_unsubscribe_success')

    # After successful submission of feedback , redirect to thank you page template
    @http.route('/unsubscribe-instock/thank-you', type='http', auth='user', website=True)
    def unsubscribe_thank_you(self):
        return request.render('sps_theme.instock_unsubscribe_success')




