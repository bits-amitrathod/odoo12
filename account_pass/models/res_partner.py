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
        ida = self.env['ir.ui.view'].sudo().create({
            'name': 'test Filter',
            'model': 'account.pass',
            'arch': """<search string='Search pass'> <field name='partner_id'/> 
            <filter string="Active Customer" domain="[('partner_id.id', '=', '""" + str(self.id) + """')]" name="active_customer"/>
            </search>"""
        })
        action = self.env['ir.actions.act_window']._for_xml_id('account_pass.account_pass_windows_action')
        action['search_view_id'] = [ida.id, 'search']
        action['context'] = {
            'search_default_active_customer': True,
        }
        return action

    def create_account_pass(self, partner_id):
         rec = self.env['account.pass'].search([('partner_id', '=',partner_id )], limit=1)
         if rec :
             return rec.id
         else:
             return self.env['account.pass'].create({'partner_id':partner_id}).id

