# -*- coding: utf-8 -*-
################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#
################################################################################
from odoo import models,fields,api
import requests
import json
import logging
_logger = logging.getLogger(__name__)
from odoo.exceptions import ValidationError

class Detail_oauth2(models.Model):
    _name = 'oauth2.detail'

    sequence_no = fields.Integer(string="Sequence No",required = True,help="Enter sequence no you want to add in your callback url")
    name = fields.Char(string="Token Name",required = True,help="Enter name to your OAuth 2.0")
    authorize_url = fields.Char(string="Authorize URL",default="https://accounts.google.com/o/oauth2/auth",readonly=True)
    token_url = fields.Char(string="Token URL",default="https://accounts.google.com/o/oauth2/token",readonly=True)
    domain_uri = fields.Char(string="Shop URL",required = True,help="Domain where You what google to authenticate")
    callback_uri = fields.Char(string="Callback URL",required=True,help="URL where You what google to authenticate",compute="_comute_callback")
    client_id = fields.Char(string="Client Id",required = True)
    client_secret = fields.Char(string="Client Secret",required = True)
    authorization_redirect_url = fields.Char(string="Authorization Redirect Url",readonly=True)
    authorization_code = fields.Char(string="Authorization Code")
    name = fields.Char(string="Token Name",required = True,help="Enter name to your OAuth 2.0")
    # =========================================================================================================================
    config_merchant_detail=fields.Boolean("Configure Merchant Detail",default=False)
    verify_account_url = fields.Char(string="URL to Verify",help="URL to verify your Website")
    verify_url_data = fields.Text(string="Data in URL",help="Data in your URL")
    merchant_id = fields.Char(string="Merchant ID",help="ID of the Merchant Account")
    # =========================================================================================================================
    auth_token = fields.Char(string="Auth Token" ,readonly=True)
    # auth_token = fields.Char(string="Auth Token")
    authentication_state = fields.Selection([('new','New'),('authorize_code','Authorize Code'),('error','Error'),('authorize_token','Authorize Token')],default='new')
    _sql_constraints = [('sequence_no_unique', 'unique(sequence_no)','Sequence No should be Unique')]

    def button_authorize_url(self):
        self.authorization_redirect_url = self.authorize_url + '?response_type=code&client_id=' + self.client_id + '&redirect_uri=' + self.callback_uri + '&scope=https://www.googleapis.com/auth/content'
        self.authentication_state = 'authorize_code'
        return {
            'type': 'ir.actions.act_url',
            'url': self.authorization_redirect_url,
            'target': '_new', # open in a new tab
        }

    def button_get_token(self):

        data = {'grant_type': 'authorization_code', 'code': self.authorization_code, 'redirect_uri': self.callback_uri}
        resp = requests.post(self.token_url, data=data, verify=False, allow_redirects=False, auth=(self.client_id, self.client_secret))
        resp = json.loads(resp.text)
        message = ""
        if resp.get('access_token'):
            try:
                self.auth_token = resp.get('access_token')
                self.authentication_state = 'authorize_token'
                message = "Completed"
            except:
                self.auth_token = None
                self.authentication_state = 'error'
                message = str(resp.get('error'))
        else:
            self.auth_token = None
            self.authentication_state = 'error'
            message = "No Data in Authentication Token, Please Check the Entered Detail and Try again"
        return message

    @api.onchange('domain_uri','sequence_no')
    def _comute_callback(self):
        if self.domain_uri and self.sequence_no:
            self.callback_uri = self.domain_uri+"/google/"+str(self.sequence_no)+"/OAuth2"
        else:
            self.callback_uri = ''
