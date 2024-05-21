import logging
import werkzeug
import odoo

from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import AccessDenied
from odoo.http import request
from odoo import http, _
from odoo.addons.auth_signup.models.res_users import SignupError
from ast import literal_eval
from odoo.tools.misc import ustr
from odoo.exceptions import UserError
from odoo.addons.web.controllers.main import ensure_db, Home
from odoo.exceptions import ValidationError
from odoo.http import Controller, request, route
from werkzeug.exceptions import Forbidden, NotFound
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


class LoginCaseInsensitive(models.Model):
    _inherit = "res.users"


    def _create_user_from_template(self, values):
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
        temp_email = values['login']
        if values['login'] == temp_email.lower():
            user = request.env['res.users'].sudo().search([('email', '=ilike', values['login'])])
            if user:
                raise ValidationError("Another user is already registered using this email address.")
            else:
                # values['login'] = values['login'].lower()
                user = super(LoginCaseInsensitive, self).create(values)
                return user
        else:
            raise ValidationError("Email address should contain small letters only.")


    @api.model
    def write(self, values):
        if 'login' in values:
            temp_email = values['login']
            if values['login'] == temp_email.lower():
                user = super(LoginCaseInsensitive, self).write(values)
            else:
                raise ValidationError("Email address should contain small letters only.")
        else:
            user = super(LoginCaseInsensitive, self).write(values)
        return user

    @classmethod
    def _login(cls, db, login, password,user_agent_env):
        if not password:
            raise AccessDenied()
        ip = request.httprequest.environ['REMOTE_ADDR'] if request else 'n/a'
        try:
            with cls.pool.cursor() as cr:
                self = api.Environment(cr, SUPERUSER_ID, {})[cls._name]
                with self._assert_can_auth():
                    user = self.search(self._get_login_domain(login))
                    if not user:
                        raise AccessDenied()
                    user = user.sudo(user.id)
                    user._check_credentials(password,user_agent_env)
                    user._update_last_login()
        except AccessDenied:
            _logger.info("Login failed for db:%s login:%s from %s", db, login, ip)
            raise

        _logger.info("Login successful for db:%s login:%s from %s", db, login, ip)

        return user.id

    # @classmethod
    # def _login(cls, db, login, password):
    #     if not password:
    #         return False
    #     user_id = False
    #     try:
    #         with cls.pool.cursor() as cr:
    #             self = api.Environment(cr, SUPERUSER_ID, {})[cls._name]
    #             user = self.search([('login', '=', login)])
    #             if user:
    #                 user_id = user.id
    #                 user.sudo(user_id).check_credentials(password)
    #                 user.sudo(user_id)._update_last_login()
    #     except AccessDenied:
    #         user_id = False
    #
    #     status = "successful" if user_id else "failed"
    #     ip = request.httprequest.environ['REMOTE_ADDR'] if request else 'n/a'
    #     _logger.info("Login %s for db:%s login:%s from %s", status, db, login, ip)
    #
    #     return user_id

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

    # @api.model
    # def _signup_create_user_new(self, values):
    #     """ create a new user from the template user """
    #     get_param = self.env['ir.config_parameter'].sudo().get_param
    #     template_user_id = literal_eval(get_param('auth_signup.template_user_id', 'False'))
    #     template_user = self.browse(template_user_id)
    #     assert template_user.exists(), 'Signup: invalid template user'
    #
    #     # check that uninvited users may sign up
    #     if 'partner_id' not in values:
    #         if not literal_eval(get_param('auth_signup.allow_uninvited', 'False')):
    #             raise SignupError(_('Signup is not allowed for uninvited users'))
    #
    #     assert values.get('login'), "Signup: no login given for new user"
    #     assert values.get('partner_id') or values.get('name'), "Signup: no name or partner given for new user"
    #
    #     # create a copy of the template user (attached to a specific partner_id if given)
    #     values['active'] = True
    #     try:
    #         with self.env.cr.savepoint():
    #             temp_email = values['email']
    #             if values['email'] == temp_email.lower():
    #                 user = request.env['res.users'].sudo().search([('email', '=ilike', values['email'])])
    #                 if user:
    #                     raise SignupError()
    #                 else:
    #                     return template_user.with_context(no_reset_password=True).copy(values)
    #             else:
    #                 raise ValidationError("Email address should contain small letters only.")
    #
    #     except Exception as e:
    #         # copy may failed if asked login is not available.
    #         if values['email'] != temp_email.lower():
    #             raise SignupError("Email address should contain small letters only.")
    #         else:
    #             raise SignupError(ustr(e))

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


class AuthSignupHome(Home):

    @http.route()
    def web_login(self, *args, **kw):
        ensure_db()
        if 'login' in kw:
            temp_email = kw['login']
            if kw['login'] != temp_email.lower():
                #raise ValidationError("Email address should contain small letters only.")
                response = self.web_login_msg(*args, **kw)
                response.qcontext.update(self.get_auth_signup_config())
                if request.httprequest.method == 'GET' and request.session.uid and request.params.get('redirect'):
                    # Redirect if already logged in and redirect param is present
                    return http.redirect_with_hash(request.params.get('redirect'))
                return response
            else:
                response = super(AuthSignupHome, self).web_login(*args, **kw)
                response.qcontext.update(self.get_auth_signup_config())
                if request.httprequest.method == 'GET' and request.session.uid and request.params.get('redirect'):
                    # Redirect if already logged in and redirect param is present
                    return http.redirect_with_hash(request.params.get('redirect'))
                return response

        else:

            response = super(AuthSignupHome, self).web_login(*args, **kw)
            response.qcontext.update(self.get_auth_signup_config())
            if request.httprequest.method == 'GET' and request.session.uid and request.params.get('redirect'):
                # Redirect if already logged in and redirect param is present
                return http.redirect_with_hash(request.params.get('redirect'))
            return response

    def web_login_msg(self, redirect=None, **kw):
        ensure_db()
        request.params['login_success'] = False
        if request.httprequest.method == 'GET' and redirect and request.session.uid:
            return http.redirect_with_hash(redirect)

        if not request.uid:
            request.uid = odoo.SUPERUSER_ID

        values = request.params.copy()
        try:
            values['databases'] = http.db_list()
        except odoo.exceptions.AccessDenied:
            values['databases'] = None

        if request.httprequest.method == 'POST':

            temp_email = request.params['login']
            if request.params['login'] != temp_email.lower():
                values['error'] = _("Email address should contain small letters only.")
            else:

                old_uid = request.uid
                uid = request.session.authenticate(request.session.db, request.params['login'], request.params['password'])
                if uid is not False:
                    request.params['login_success'] = True
                    return http.redirect_with_hash(self._login_redirect(uid, redirect=redirect))
                request.uid = old_uid
                values['error'] = _("Wrong login/password")
        else:
            if 'error' in request.params and request.params.get('error') == 'access':
                values['error'] = _('Only employee can access this database. Please contact the administrator.')

        if 'login' not in values and request.session.get('auth_login'):
            values['login'] = request.session.get('auth_login')

        if not odoo.tools.config['list_db']:
            values['disable_database_manager'] = True

        response = request.render('web.login', values)
        response.headers['X-Frame-Options'] = 'DENY'
        return response

    @http.route('/web/signup', type='http', auth='public', website=True, sitemap=False)
    def web_auth_signup(self, *args, **kw):
        qcontext = self.get_auth_signup_qcontext()

        if not qcontext.get('token') and not qcontext.get('signup_enabled'):
            raise werkzeug.exceptions.NotFound()

        if 'error' not in qcontext and request.httprequest.method == 'POST':
            try:
                self.do_signup(qcontext)
                # Send an account creation confirmation email
                if qcontext.get('token'):
                    temp_email = qcontext.get('login')
                    if qcontext.get('login') == temp_email.lower():
                        user_sudo = request.env['res.users'].sudo().search([('login', '=', qcontext.get('login'))])
                        template = request.env.ref('auth_signup.mail_template_user_signup_account_created', raise_if_not_found=False)
                        if user_sudo and template:
                            template.sudo().with_context(
                                lang=user_sudo.lang,
                                auth_login=werkzeug.url_encode({'auth_login': user_sudo.email}),
                            ).send_mail(user_sudo.id, force_send=False)
                    else:
                        raise ValidationError("Email address should contain small letters only.")

                return super(AuthSignupHome, self).web_login(*args, **kw)
            except UserError as e:
                qcontext['error'] = e.name or e.value
            except (SignupError, AssertionError) as e:
                temp_email = qcontext.get('login')
                if request.env["res.users"].sudo().search([("login", "=ilike", qcontext.get("login"))]):
                    qcontext["error"] = _("Another user is already registered using this email address.")
                elif qcontext.get('login') != temp_email.lower():
                    qcontext["error"] = _("Email address should contain small letters only.")
                else:
                    _logger.error("%s", e)
                    qcontext['error'] = _("Could not create a new account.")

        response = request.render('auth_signup.signup', qcontext)
        response.headers['X-Frame-Options'] = 'DENY'
        return response


    @http.route('/web/reset_password', type='http', auth='public', website=True, sitemap=False)
    def web_auth_reset_password(self, *args, **kw):
        qcontext = self.get_auth_signup_qcontext()

        if not qcontext.get('token') and not qcontext.get('reset_password_enabled'):
            raise werkzeug.exceptions.NotFound()

        if 'error' not in qcontext and request.httprequest.method == 'POST':
            try:
                if qcontext.get('token'):
                    self.do_signup(qcontext)
                    return super(AuthSignupHome, self).web_login(*args, **kw)
                else:
                    login = qcontext.get('login')
                    if login != login.lower():
                        qcontext['error'] = _("Email address should contain small letters only.")
                    else:
                        assert login, _("No login provided.")
                        _logger.info(
                            "Password reset attempt for <%s> by user <%s> from %s",
                            login, request.env.user.login, request.httprequest.remote_addr)
                        request.env['res.users'].sudo().reset_password_new(login)
                        qcontext['message'] = _("An email has been sent with credentials to reset your password")
            except UserError as e:
                qcontext['error'] = e.name or e.value
            except SignupError:
                qcontext['error'] = _("Could not reset your password")
                _logger.exception('error when resetting password')
            except Exception as e:
                qcontext['error'] = str(e)

        response = request.render('auth_signup.reset_password', qcontext)
        response.headers['X-Frame-Options'] = 'DENY'
        return response

    def get_auth_signup_config(self):
        """retrieve the module config (which features are enabled) for the login page"""

        get_param = request.env['ir.config_parameter'].sudo().get_param
        return {
            'signup_enabled': request.env['res.users']._get_signup_invitation_scope() == 'b2c',
            'reset_password_enabled': get_param('auth_signup.reset_password') == 'True',
        }

    def get_auth_signup_qcontext(self):
        """ Shared helper returning the rendering context for signup and reset password """
        qcontext = request.params.copy()
        qcontext.update(self.get_auth_signup_config())
        if not qcontext.get('token') and request.session.get('auth_signup_token'):
            qcontext['token'] = request.session.get('auth_signup_token')
        if qcontext.get('token'):
            try:
                # retrieve the user info (name, login or email) corresponding to a signup token
                token_infos = request.env['res.partner'].sudo().signup_retrieve_info(qcontext.get('token'))
                for k, v in token_infos.items():
                    qcontext.setdefault(k, v)
            except:
                qcontext['error'] = _("Invalid signup token")
                qcontext['invalid_token'] = True
        return qcontext

    def do_signup(self, qcontext):
        """ Shared helper that creates a res.partner out of a token """
        values = { key: qcontext.get(key) for key in ('login', 'name', 'password') }
        if not values:
            raise UserError(_("The form was not properly filled in."))
        if values.get('password') != qcontext.get('confirm_password'):
            raise UserError(_("Passwords do not match; please retype them."))
        supported_langs = [lang['code'] for lang in request.env['res.lang'].sudo().search_read([], ['code'])]
        if request.lang in supported_langs:
            values['lang'] = request.lang
        self._signup_with_values(qcontext.get('token'), values)
        request.env.cr.commit()

    def _signup_with_values(self, token, values):
        db, login, password = request.env['res.users'].sudo().signupnew(values, token)
        request.env.cr.commit()     # as authenticate will use its own cursor we need to commit the current transaction
        uid = request.session.authenticate(db, login, password)
        if not uid:
            raise SignupError(_('Authentication Failed.'))


class CustomerPortal(Controller):

    MANDATORY_BILLING_FIELDS = ["name", "phone", "email", "street", "city", "country_id"]
    OPTIONAL_BILLING_FIELDS = ["zipcode", "state_id", "vat", "company_name"]

    @route(['/my/account'], type='http', auth='user', website=True)
    def account(self, redirect=None, **post):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        values.update({
            'error': {},
            'error_message': [],
        })

        if post and request.httprequest.method == 'POST':
            error, error_message = self.details_form_validate_new(post)
            values.update({'error': error, 'error_message': error_message})
            values.update(post)
            if not error:
                values = {key: post[key] for key in self.MANDATORY_BILLING_FIELDS}
                values.update({key: post[key] for key in self.OPTIONAL_BILLING_FIELDS if key in post})
                for field in set(['country_id', 'state_id']) & set(values.keys()):
                    try:
                        values[field] = int(values[field])
                    except:
                        values[field] = False
                values.update({'zip': values.pop('zipcode', '')})
                partner.sudo().write(values)
                if redirect:
                    return request.redirect(redirect)
                return request.redirect('/my/home')

        countries = request.env['res.country'].sudo().search([])
        states = request.env['res.country.state'].sudo().search([])

        values.update({
            'partner': partner,
            'countries': countries,
            'states': states,
            'has_check_vat': hasattr(request.env['res.partner'], 'check_vat'),
            'redirect': redirect,
            'page_name': 'my_details',
        })

        response = request.render("portal.portal_my_details", values)
        response.headers['X-Frame-Options'] = 'DENY'
        return response

    def details_form_validate_new(self, data):
        error = dict()
        error_message = []

        # Validation
        for field_name in self.MANDATORY_BILLING_FIELDS:
            if not data.get(field_name):
                error[field_name] = 'missing'

        # email validation
        if data.get('email') and not tools.single_email_re.match(data.get('email')):
            error["email"] = 'error'
            error_message.append(_('Invalid Email! Please enter a valid email address.'))

        if data.get('email') != data.get('email').lower():
            error["email"] = 'error'
            error_message.append(_('Email address should contain small letters only.'))

        # vat validation
        partner = request.env["res.partner"]
        if data.get("vat") and hasattr(partner, "check_vat"):
            if data.get("country_id"):
                data["vat"] = request.env["res.partner"].fix_eu_vat_number(int(data.get("country_id")), data.get("vat"))
            partner_dummy = partner.new({
                'vat': data['vat'],
                'country_id': (int(data['country_id'])
                               if data.get('country_id') else False),
            })
            try:
                partner_dummy.check_vat()
            except ValidationError:
                error["vat"] = 'error'

        # error message for empty required fields
        if [err for err in error.values() if err == 'missing']:
            error_message.append(_('Some required fields are empty.'))

        unknown = [k for k in data if k not in self.MANDATORY_BILLING_FIELDS + self.OPTIONAL_BILLING_FIELDS]
        if unknown:
            error['common'] = 'Unknown field'
            error_message.append("Unknown field '%s'" % ','.join(unknown))

        return error, error_message


    def _prepare_portal_layout_values(self):
        # get customer sales rep
        sales_user = False
        partner = request.env.user.partner_id
        if partner.user_id and not partner.user_id._is_public():
            sales_user = partner.user_id

        return {
            'sales_user': sales_user,
            'page_name': 'home',
            'archive_groups': [],
        }

class ResPartner(models.Model):
    _inherit = 'res.partner'

    signup_token = fields.Char(copy=False)
    signup_type = fields.Char(string='Signup Token Type', copy=False)
    signup_expiration = fields.Datetime(copy=False)
# class WebsiteSale(http.Controller):
#
#     def _get_mandatory_billing_fields(self):
#         return ["name", "email", "street", "city", "country_id"]
#
#     def _get_mandatory_shipping_fields(self):
#         return ["name", "street", "city", "country_id"]
#
#     def _checkout_form_save(self, mode, checkout, all_values):
#         Partner = request.env['res.partner']
#         if mode[0] == 'new':
#             checkout['saleforce_ac'] = Partner.sudo().env['ir.sequence'].next_by_code('sale.force.no') or _('New')
#             partner_id = Partner.sudo().create(checkout).id
#         elif mode[0] == 'edit':
#             partner_id = int(all_values.get('partner_id', 0))
#             if partner_id:
#                 # double check
#                 order = request.website.sale_get_order()
#                 shippings = Partner.sudo().search([("id", "child_of", order.partner_id.commercial_partner_id.ids)])
#                 if partner_id not in shippings.mapped('id') and partner_id != order.partner_id.id:
#                     return Forbidden()
#                 Partner.browse(partner_id).sudo().write(checkout)
#         return partner_id
#
#     @http.route(['/shop/address'], type='http', methods=['GET', 'POST'], auth="public", website=True)
#     def address(self, **kw):
#         Partner = request.env['res.partner'].with_context(show_address=1).sudo()
#         order = request.website.sale_get_order()
#
#         redirection = self.checkout_redirection(order)
#         if redirection:
#             return redirection
#
#         mode = (False, False)
#         def_country_id = order.partner_id.country_id
#         values, errors = {}, {}
#
#         partner_id = int(kw.get('partner_id', -1))
#
#         # IF PUBLIC ORDER
#         if order.partner_id.id == request.website.user_id.sudo().partner_id.id:
#             mode = ('new', 'billing')
#             country_code = request.session['geoip'].get('country_code')
#             if country_code:
#                 def_country_id = request.env['res.country'].search([('code', '=', country_code)], limit=1)
#             else:
#                 def_country_id = request.website.user_id.sudo().country_id
#         # IF ORDER LINKED TO A PARTNER
#         else:
#             if partner_id > 0:
#                 if partner_id == order.partner_id.id:
#                     mode = ('edit', 'billing')
#                 else:
#                     shippings = Partner.search([('id', 'child_of', order.partner_id.commercial_partner_id.ids)])
#                     if partner_id in shippings.mapped('id'):
#                         mode = ('edit', 'shipping')
#                     else:
#                         return Forbidden()
#                 if mode:
#                     values = Partner.browse(partner_id)
#             elif partner_id == -1:
#                 mode = ('new', 'shipping')
#             else:  # no mode - refresh without post?
#                 return request.redirect('/shop/checkout')
#
#         # IF POSTED
#         if 'submitted' in kw:
#             pre_values = self.values_preprocess(order, mode, kw)
#             errors, error_msg = self.checkout_form_validate(mode, kw, pre_values)
#             post, errors, error_msg = self.values_postprocess(order, mode, pre_values, errors, error_msg)
#
#             if errors:
#                 errors['error_message'] = error_msg
#                 values = kw
#             else:
#                 partner_id = self._checkout_form_save(mode, post, kw)
#
#                 if mode[1] == 'billing':
#                     order.partner_id = partner_id
#                     order.onchange_partner_id()
#                 elif mode[1] == 'shipping':
#                     order.partner_shipping_id = partner_id
#
#                 order.message_partner_ids = [(4, partner_id), (3, request.website.partner_id.id)]
#                 if not errors:
#                     return request.redirect(kw.get('callback') or '/shop/checkout')
#
#         country = 'country_id' in values and values['country_id'] != '' and request.env['res.country'].browse(
#             int(values['country_id']))
#         country = country and country.exists() or def_country_id
#         #'country': country,
#         render_values = {
#             'website_sale_order': order,
#             'partner_id': partner_id,
#             'mode': mode,
#             'checkout': values,
#             'country': country,
#             'countries': country.get_website_sale_countries(mode=mode[1]),
#             "states": country.get_website_sale_states(mode=mode[1]),
#             'error': errors,
#             'callback': kw.get('callback'),
#         }
#         return request.render("website_sale.address", render_values)
#
#     def checkout_redirection(self, order):
#         # must have a draft sales order with lines at this point, otherwise reset
#         if not order or order.state != 'draft':
#             request.session['sale_order_id'] = None
#             request.session['sale_transaction_id'] = None
#             return request.redirect('/shop')
#
#         if order and not order.order_line:
#             return request.redirect('/shop/cart')
#
#         # if transaction pending / done: redirect to confirmation
#         tx = request.env.context.get('website_sale_transaction')
#         if tx and tx.state != 'draft':
#             return request.redirect('/shop/payment/confirmation/%s' % order.id)
#
#     def values_preprocess(self, order, mode, values):
#         return values
#
#     def checkout_form_validate(self, mode, all_form_values, data):
#         # mode: tuple ('new|edit', 'billing|shipping')
#         # all_form_values: all values before preprocess
#         # data: values after preprocess
#         error = dict()
#         error_message = []
#
#         # Required fields from form
#         required_fields = [f for f in (all_form_values.get('field_required') or '').split(',') if f]
#         # Required fields from mandatory field function
#         required_fields += mode[1] == 'shipping' and self._get_mandatory_shipping_fields() or self._get_mandatory_billing_fields()
#         # Check if state required
#         country = request.env['res.country']
#         if data.get('country_id'):
#             country = country.browse(int(data.get('country_id')))
#             if 'state_code' in country.get_address_fields() and country.state_ids:
#                 required_fields += ['state_id']
#
#         # error message for empty required fields
#         for field_name in required_fields:
#             if not data.get(field_name):
#                 error[field_name] = 'missing'
#
#         # email validation
#         if data.get('email') and not tools.single_email_re.match(data.get('email')):
#             error["email"] = 'error'
#             error_message.append(_('Invalid Email! Please enter a valid email address.'))
#
#         if data.get('email') is not None and data.get('email') != data.get('email').lower():
#             error["email"] = 'error'
#             error_message.append(_('Email address should contain small letters only.'))
#
#         # vat validation
#         Partner = request.env['res.partner']
#         if data.get("vat") and hasattr(Partner, "check_vat"):
#             if data.get("country_id"):
#                 data["vat"] = Partner.fix_eu_vat_number(data.get("country_id"), data.get("vat"))
#             partner_dummy = Partner.new({
#                 'vat': data['vat'],
#                 'country_id': (int(data['country_id'])
#                                if data.get('country_id') else False),
#             })
#             try:
#                 partner_dummy.check_vat()
#             except ValidationError:
#                 error["vat"] = 'error'
#
#         if [err for err in error.values() if err == 'missing']:
#             error_message.append(_('Some required fields are empty.'))
#
#         return error, error_message
#
#
#     def values_postprocess(self, order, mode, values, errors, error_msg):
#         new_values = {}
#         authorized_fields = request.env['ir.model']._get('res.partner')._get_form_writable_fields()
#         for k, v in values.items():
#             # don't drop empty value, it could be a field to reset
#             if k in authorized_fields and v is not None:
#                 new_values[k] = v
#             else:  # DEBUG ONLY
#                 if k not in ('field_required', 'partner_id', 'callback', 'submitted'): # classic case
#                     _logger.debug("website_sale postprocess: %s value has been dropped (empty or not writable)" % k)
#
#         new_values['customer_rank'] = 1
#         new_values['team_id'] = request.website.salesteam_id and request.website.salesteam_id.id
#         new_values['user_id'] = request.website.salesperson_id and request.website.salesperson_id.id
#
#         lang = request.lang if request.lang in request.website.mapped('language_ids.code') else None
#         if lang:
#             new_values['lang'] = lang
#         if mode == ('edit', 'billing') and order.partner_id.type == 'contact':
#             new_values['type'] = 'other'
#         if mode[1] == 'shipping':
#             new_values['parent_id'] = order.partner_id.commercial_partner_id.id
#             new_values['type'] = 'delivery'
#
#         return new_values, errors, error_msg

