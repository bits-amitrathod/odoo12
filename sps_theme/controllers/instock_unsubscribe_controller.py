# controllers/main.py
from pickle import FALSE

from odoo import http
from odoo.http import request
from datetime import date

class InStockUnsubscribe(http.Controller):



    # This method is written to load parent company and related contacts to template.
    @http.route('/unsubscribe-instock', type='http', auth='user', website=True)
    def unsubscribe_form(self, **kwargs):
        user_partner = request.env.user.partner_id
        parent_company = user_partner.parent_id or user_partner

        # Include the parent company and all its child companies
        related_companies = request.env['res.partner'].sudo().search([
            ('id', 'child_of', parent_company.id),
            ('is_company', '=', True)
        ])

        # Get all contacts (not companies) under those companies, with valid email and no end_date
        contacts = request.env['res.partner'].sudo().search([
            ('parent_id', 'in', related_companies.ids),
            ('type', '=', 'contact'),  # Only actual contact records
            ('email', '!=', False),
            ('end_date', '=', False),
        ])

        return request.render('sps_theme.instock_unsubscriber_page_template', {
            'contacts': contacts,
            'company': parent_company,
        })


    # Method used to submit unsubscribe feedback for checked/selected contacts and set end date as todays date with unsubscribe reason.
    @http.route('/unsubscribe-instock/submit', type='http', auth='user', methods=['POST'], csrf=True , website=True)
    def unsubscribe_submit(self, **post):
        contact_ids = request.httprequest.form.getlist('contact_ids')
        feedback = post.get('feedback')
        # feedback = request.params.get('feedback')

        if not contact_ids or not feedback:
            return request.redirect('/unsubscribe-instock?error=missing_data')

        contacts = request.env['res.partner'].browse([int(cid) for cid in contact_ids])
        today = date.today()

        for contact in contacts:
            contact.write({
                'end_date': today,
                'unsubscribe_feedback': feedback
            })

        return request.render('sps_theme.instock_unsubscribe_success')



    # After successful submission of feedback , redirect to thank you page template
    @http.route('/unsubscribe-instock/thank-you', type='http', auth='user', website=True)
    def unsubscribe_thank_you(self):
        return request.render('sps_theme.instock_unsubscribe_success')




