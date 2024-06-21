from odoo import api,fields, models, tools, _

import logging
_logger = logging.getLogger(__name__)

class Partner(models.Model):
    _inherit = "res.partner"

    def action_account_pass(self):
        """
        Create a new view for the search filter
        Args:
            self (obj): The current object
        Returns:
            obj: The created ir.ui.view record
        """
        # Create a new view for the search filter
        ida = self.env['ir.ui.view'].sudo().create({
            'name': 'test Filter',
            'model': 'account.pass',
            'arch': """<search string='Search pass'> <field name='partner_id'/> 
            <filter string="Active Customer" domain="[('partner_id.id', '=', '""" + str(self.id) + """')]" name="active_customer"/>
            </search>"""
        })
        # Get the action for the account pass window
        action = self.env['ir.actions.act_window']._for_xml_id('account_pass.account_pass_windows_action')
        # Set the search view ID and context for the action
        action['search_view_id'] = [ida.id, 'search']
        action['context'] = {'search_default_active_customer': True,}
        return action

    def create_account_pass(self, partner_id):
        """
        Create a new account.pass record for the given partner_id.

        :param int partner_id: the id of the partner to create the account.pass record for
        :return: the id of the newly created account.pass record
        :rtype: int
        """

        # Get the account pass model
        account_pass = self.env['account.pass']
        # Search for an existing account pass for the partner
        existing = account_pass.search([('partner_id', '=', partner_id)], limit=1)
        # If an existing account pass is found, return its ID
        if existing:
            return existing.id
        else:
            # Create a new account pass for the partner
            return self.env['account.pass'].create({'partner_id': partner_id}).id
