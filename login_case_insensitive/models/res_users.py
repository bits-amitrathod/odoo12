import logging

from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo import http, _
from odoo.addons.auth_signup.models.res_users import SignupError
from ast import literal_eval
from odoo.tools.misc import ustr
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
from odoo.http import Controller, request, route
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

class ResUsers(models.Model):
    _inherit = "res.users"


    def _create_user_from_template(self, values):
        """
        Creates a new user by copying the template user and updating the given values.

        :param values: The values to update on the template user.
        :return: The created user.
        """
        template_user_id = literal_eval(self.env['ir.config_parameter'].sudo().get_param('base.template_portal_user_id', 'False'))
        template_user = self.browse(template_user_id)
        if not template_user.exists():
            raise ValueError(_('Signup: invalid template user'))


        if not values.get('login'):
            raise ValueError(_('Signup: no login given for new user'))
        if not values.get('partner_id') and not values.get('name'):
            raise ValueError(_('Signup: no name or partner given for new user'))

        # create a copy of the template user (attached to a specific partner_id if given)
        values['active'] = True
        values['customer_rank'] = 1
        try:
            with self.env.cr.savepoint():
                return template_user.with_context(no_reset_password=True).copy(values)
        except Exception as e:
            # copy may failed if asked login is not available.
            raise SignupError(ustr(e))

    @api.model
    def create(self, values):
        login = values['login']
        if login == login.lower():
            user = request.env['res.users'].sudo().search([('email', '=ilike', login)])
            if user:
                raise ValidationError("Another user is already registered using this email address.")
            else:
                user = super(ResUsers, self).create(values)
                return user
        else:
            raise ValidationError("Email address should contain small letters only.")


    @api.model
    def write(self, values):
        if 'login' in values:
            login = values['login']
            if login == login.lower():
                user = super(ResUsers, self).write(values)
            else:
                raise ValidationError("Email address should contain small letters only.")
        else:
            user = super(ResUsers, self).write(values)
        return user


    @api.model
    def signupnew(self, values, token=None):
        """ signup a user, to either:
            - create a new user (no token), or
            - create a user for a partner (with token, but no user for partner), or
            - change the password of a user (with token, and existing user).
            :param values: a dictionary with field values that are written on user
            :param token: signup token (optional)
            :return: (dbname, login, password) for the signed up user
        """
        if token:
            # signup with a token: find the corresponding partner id
            partner = self.env['res.partner']._signup_retrieve_partner(token, check_validity=True, raise_exception=True)
            # invalidate signup token
            partner.write({'signup_token': False, 'signup_type': False, 'signup_expiration': False,
                           'supplier_rank': 1})

            account_payment_term = self.env['account.payment.term'].search([('name', '=', 'Net 30'),
                                                                            ('active', '=', True)])
            if account_payment_term:
                partner.write({'property_payment_term_id': account_payment_term.id,
                               'property_supplier_payment_term_id': account_payment_term.id})

            partner_user = partner.user_ids and partner.user_ids[0] or False

            # avoid overwriting existing (presumably correct) values with geolocation data
            if partner.country_id or partner.zip or partner.city:
                values.pop('city', None)
                values.pop('country_id', None)
            if partner.lang:
                values.pop('lang', None)

            if partner_user:
                # user exists, modify it according to values
                values.pop('login', None)
                values.pop('name', None)
                partner_user.write(values)
                return (self.env.cr.dbname, partner_user.login, values.get('password'))
            else:
                # user does not exist: sign up invited user
                values.update({
                    'name': partner.name,
                    'partner_id': partner.id,
                    'email': values.get('email') or values.get('login'),
                })
                if partner.company_id:
                    values['company_id'] = partner.company_id.id
                    values['company_ids'] = [(6, 0, [partner.company_id.id])]
                self._create_user_from_template(values)
        else:
            # no token, sign up an external user
            values['saleforce_ac'] = self.env['ir.sequence'].next_by_code('sale.force.no') or _('New')
            values['email'] = values.get('email') or values.get('login')
            values['supplier_rank'] = 1
            account_payment_term = self.env['account.payment.term'].search([('name', '=', 'Net 30'), ('active', '=', True)])
            if account_payment_term:
                values['property_payment_term_id'] = account_payment_term.id
                values['property_supplier_payment_term_id'] = account_payment_term.id
            res_user = self.env['res.users'].search([('partner_id.name', '=', 'Surgical Product Solutions')])
            if res_user:
                values['user_id'] = res_user.id
            self._create_user_from_template(values)

        return (self.env.cr.dbname, values.get('login'), values.get('password'))


    def reset_password_new(self, login):
        """ retrieve the user corresponding to login (login or email),
            and reset their password
        """
        users = self.search([('login', '=', login)])
        if not users:
            users = self.search([('email', '=ilike', login)])
        if len(users) != 1:
            raise Exception(_('Reset password: invalid username or email'))
        return users.action_reset_password_new()

    def action_reset_password_new(self):
        """ create signup token for each user, and send their signup url by email """
        if self.env.context.get('install_mode', False):
            return
        if self.filtered(lambda user: not user.active):
            raise UserError(_("You cannot perform this action on an archived user."))
        # prepare reset password signup
        create_mode = bool(self.env.context.get('create_user'))

        # no time limit for initial invitation, only for reset password
        expiration = False if create_mode else self.now(days=+1)

        self.mapped('partner_id').signup_prepare(signup_type="reset", expiration=expiration)

        # send email to users with their signup url
        template = False
        if create_mode:
            try:
                template = self.env.ref('auth_signup.set_password_email', raise_if_not_found=False)
            except ValueError:
                pass
        if not template:
            template = self.env.ref('auth_signup.reset_password_email')
        assert template._name == 'mail.template'

        template_values = {
            'email_to': '${object.email|safe}',
            'email_cc': False,
            'auto_delete': True,
            'partner_to': False,
            'scheduled_date': False,
        }
        template.write(template_values)

        for user in self:
            if not user.email:
                raise UserError(_("Cannot send email: user %s has no email address.", user.name))
            # TDE FIXME: make this template technical (qweb)
            with self.env.cr.savepoint():
                #force_send = not(self.env.context.get('import_file', False))
                template.send_mail(user.id, force_send=False, raise_exception=True)
            _logger.info("Password reset email sent for user <%s> to <%s>", user.login, user.email)

    def now(self, **kwargs):
        return datetime.now() + timedelta(**kwargs)