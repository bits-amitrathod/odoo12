import logging
from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo import http, _
from odoo.exceptions import ValidationError
from odoo.http import Controller, request, route

_logger = logging.getLogger(__name__)


class CustomerPortal(Controller):
    """
       This class handles the requests to the /my/account endpoint.
    """

    MANDATORY_BILLING_FIELDS = ["name", "phone", "email", "street", "city", "country_id"]
    OPTIONAL_BILLING_FIELDS = ["zipcode", "state_id", "vat", "company_name"]

    @route(['/my/account'], type='http', auth='user', website=True)
    def account(self, redirect=None, **post):
        """
            This function handles the requests to the /my/account endpoint.

            :param redirect: the URL to redirect to after saving the details
            :type redirect: str
            :param post: the form data submitted by the user
            :type post: dict
            :return: a response object containing the rendered template
            :rtype: odoo.http.Response
        """

        # Prepare default values
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        values.update({'error': {}, 'error_message': []})

        countries = request.env['res.country'].sudo().search([])
        states = request.env['res.country.state'].sudo().search([])

        if post and request.httprequest.method == 'POST':
            error, error_message = self.details_form_validate_new(post)
            values.update({'error': error, 'error_message': error_message})
            values.update(post)

            if not error:
                # Extract billing fields
                billing_fields = {key: post[key] for key in self.MANDATORY_BILLING_FIELDS}
                billing_fields.update({key: post[key] for key in self.OPTIONAL_BILLING_FIELDS if key in post})

                # Convert country_id and state_id to integers
                for field in ['country_id', 'state_id']:
                    billing_fields[field] = int(billing_fields.get(field, 0) or 0)

                # Update zip field
                billing_fields['zip'] = billing_fields.pop('zipcode', '')

                # Update partner with billing fields
                partner.sudo().write(billing_fields)

                # Redirect if specified
                if redirect:
                    return request.redirect(redirect)
                return request.redirect('/my/home')

        values.update({
            'partner': partner,
            'countries': countries,
            'states': states,
            'has_check_vat': hasattr(request.env['res.partner'], 'check_vat'),
            'redirect': redirect,
            'page_name': 'my_details',
        })

        # Render template with updated values
        response = request.render("portal.portal_my_details", values)
        response.headers['X-Frame-Options'] = 'DENY'
        return response


    def details_form_validate_new(self, data):
        """
            Validate the data submitted in the customer details form.

            :param data: the form data submitted by the user
            :type data: dict
            :return: a dictionary containing any errors, and an error message

        """
        error = dict()
        error_message = []

        # Check for missing mandatory fields
        for field_name in self.MANDATORY_BILLING_FIELDS:
            if not data.get(field_name):
                error[field_name] = 'missing'

        # Check email validation
        email = data.get('email')
        if email:
            if not tools.single_email_re.match(email):
                error["email"] = 'error'
                error_message.append(_('Invalid Email! Please enter a valid email address.'))
            elif email != email.lower():
                error["email"] = 'error'
                error_message.append(_('Email address should contain small letters only.'))


        # vat validation
        vat = data.get("vat")
        country_id = data.get("country_id")
        res_partner = request.env["res.partner"]
        if vat and hasattr(res_partner, "check_vat") and country_id:
            vat = res_partner.fix_eu_vat_number(int(country_id), vat)
            partner_dummy = res_partner.new({
                'vat': vat,
                'country_id': int(country_id) if country_id else False,
            })
            try:
                partner_dummy.check_vat()
            except ValidationError:
                error["vat"] = 'error'

        # error message for empty required fields
        if [err for err in error.values() if err == 'missing']:
            error_message.append(_('Some required fields are empty.'))
        if any(err == 'missing' for err in error.values()):
            error_message.append(_('Some required fields are empty.'))

        unknown = [k for k in data if k not in self.MANDATORY_BILLING_FIELDS + self.OPTIONAL_BILLING_FIELDS]
        if unknown:
            error['common'] = 'Unknown field'
            error_message.append("Unknown field '%s'" % ','.join(unknown))

        return error, error_message


    def _prepare_portal_layout_values(self):
        # get customer sales rep
        partner = request.env.user.partner_id
        sales_user = partner.user_id if partner.user_id and not partner.user_id._is_public() else False

        return {
            'sales_user': sales_user,
            'page_name': 'home',
            'archive_groups': [],
        }
