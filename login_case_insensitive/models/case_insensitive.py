import logging
import werkzeug
import odoo

from odoo import http, _
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.exceptions import UserError
from odoo.addons.web.controllers.home import ensure_db, Home
from odoo.exceptions import ValidationError
from odoo.http import Controller, request, route
from werkzeug.exceptions import Forbidden, NotFound

_logger = logging.getLogger(__name__)


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
