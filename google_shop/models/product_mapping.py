# -*- coding: utf-8 -*-
################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#
################################################################################
from odoo import models,fields,api
import logging
import requests
import json
_logger = logging.getLogger(__name__)
from odoo.addons.http_routing.models.ir_http import slug
from odoo.exceptions import UserError


class ProductMapping(models.Model):
    _name = 'product.mapping'

    google_shop_id = fields.Many2one(comodel_name='google.shop',string="Shop Name",required = True)
    product_id = fields.Many2one(comodel_name='product.product',string="Product Name",required = True)
    update_status = fields.Boolean(string="Updated",default=True)
    product_status = fields.Selection([('updated','Done'),('error','Error')])
    google_product_id = fields.Char(string="Google Product Id")
    message = fields.Char(string="Message")

    @api.depends('google_shop_id', 'product_id')
    def name_get(self):
        result = []
        for mapping in self:
            name = "[" + mapping.google_shop_id.name + "]" + ' ' + mapping.product_id.name
            result.append((mapping.id, name))
        return result


    def delete_mapping(self,oauth_token,merchant_id):
        if self.product_status == "error":
            self.unlink()
            return "1"

        try:

            api_call_headers = {'Authorization': "Bearer "+oauth_token}
            api_call_response = requests.delete('https://www.googleapis.com/content/v2.1/'+merchant_id+'/products/'+self.google_product_id, headers=api_call_headers, verify=False)

        except Exception as e:
            return "2"
            # raise UserError("OAuth2 or Merchant Id might be wrong \n Please Verify It")
        if api_call_response.status_code == 401:
            return "3"
            # message="Account ID might had been expired so, refresh it and try again"
        if api_call_response.status_code == 204:
            self.unlink()
            return "1"
        else:
            error_message = json.loads(api_call_response.text).get('error').get('message')
            if error_message != "item not found":
                return error_message
            else:
                self.unlink()
                return "1"
