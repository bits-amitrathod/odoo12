# -*- coding: utf-8 -*-
################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#
################################################################################
from odoo import http
import logging
_logger = logging.getLogger(__name__)
import werkzeug

class Google(http.Controller):
    @http.route('/google/<int:sequence_no>/OAuth2',type="http",method=["POST"],auth="public",csrf=False,website=True)
    def oauth2_verify(self,sequence_no, **kw):
        b=""
        try:
            if (kw.get("code")):
                a=http.request.env['oauth2.detail'].sudo().search([('sequence_no','=',sequence_no)],limit=1)
                a.write({'authorization_code': kw.get("code")})
                b=a.button_get_token()
                _logger.info("_____First Call_______%r",b)
                if(b == 'Completed'):
                    return http.request.render('google_shop.success_view',{})
                else:
                    return http.request.render('google_shop.error_view_1',{'message':b})
            else:
                _logger.info("_____No Data_______%r",b)
                return http.request.render('google_shop.error_view_1',{'message':"Somethiong went wrong as the redirect URL entered might be Wrong"})

        except:
            _logger.info("________Other Error____________%r",b)
            return http.request.render('google_shop.error_view_1',{'message':"Something went Wrong, Please Try Again"})

    @http.route('/r/<string:html_file>',type="http",method=["POST"],auth="public",csrf=False,website=True)
    def website_verify(self,html_file,**kw):
        rec = http.request.env["oauth2.detail"].sudo().search([('verify_account_url','=',html_file)],limit=1)
        if rec:
            return rec.verify_url_data
        else:
            html = http.request.env['ir.ui.view'].render_template('website.page_404', {})
            return werkzeug.wrappers.Response(html, status=404, content_type='text/html;charset=utf-8')
