from odoo import api,fields, models, tools, _
from odoo.osv import expression
import re
from odoo.osv.expression import get_unaccent_wrapper
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)

class Partner(models.Model):
    _inherit = "res.partner"

    def action_account_pass(self):
        form_view_id = self.env.ref('account_pass.account_pass_view_form').id
        id = self.create_account_pass(self.id)
        # action = {
        #     'type': 'ir.actions.act_window',
        #     'views': [(form_view_id, 'form')],
        #     'view_mode': 'form',
        #     'name': 'Account Pass Form',
        #     'res_model': 'account.pass',
        #     'domain': [('partner_id', '=', id)]
        # }
        action = self.env['ir.actions.act_window']._for_xml_id('account_pass.account_pass_windows_action')
        action['domain'] = [('partner_id', '=', self.id)]
        return action

    def create_account_pass(self, partner_id):
         rec = self.env['account.pass'].search([('partner_id', '=',partner_id )], limit=1)
         if rec :
             return rec.id
         else:
             return self.env['account.pass'].create({'partner_id':partner_id}).id

