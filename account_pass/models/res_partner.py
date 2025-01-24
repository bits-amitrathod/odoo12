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

    def _get_unreconciled_aml_domain(self):
        self.env['account.move.line'].search([('reconciled', '=', False), ('account_id.deprecated', '=', False),
                                              ('account_id.account_type', '=', 'asset_receivable'),
                                              ('parent_state', '=', 'posted'), ('partner_id', 'in', self.ids),
                                              ('company_id', '=', self.env.company.id),
                                              ('move_type', 'in', ('entry', 'out_refund'))]).write({'blocked': True})

        return [
            ('reconciled', '=', False),
            ('account_id.deprecated', '=', False),
            ('account_id.account_type', '=', 'asset_receivable'),
            ('parent_state', '=', 'posted'),
            ('partner_id', 'in', self.ids),
            ('company_id', '=', self.env.company.id),
            ('move_type', 'not in', ('entry', 'out_refund'))

        ]


    '''Query Modifications-
    Dynamically calculate the maximum follow-up delay
    Dynamically determine the follow-up level based on overdue days
    Map the dynamic follow-up delay to the follow-up line '''

    def _get_followup_data_query(self, partner_ids=None):
        return f"""
           SELECT partner.id as partner_id,
                  ful.id as followup_line_id,
                  CASE
                       WHEN in_need_of_action_aml.id IS NOT NULL AND (prop_date.value_datetime IS NULL OR prop_date.value_datetime::date <= %(current_date)s) THEN 'in_need_of_action'
                       WHEN exceeded_unreconciled_aml.id IS NOT NULL THEN 'with_overdue_invoices'
                       WHEN partner.balance = 0 THEN 'no_action_needed'
                       ELSE 'no_action_needed' END as followup_status
           FROM (
         SELECT partner.id,
         
               --  Dynamically calculate the maximum follow-up delay
                MAX(ful.delay) as followup_delay,
                SUM(aml.balance) as balance
           FROM res_partner partner
           JOIN account_move_line aml ON aml.partner_id = partner.id
           JOIN account_account account ON account.id = aml.account_id
           
           -- Dynamically determine the follow-up level based on overdue days
      LEFT JOIN account_followup_followup_line ful ON ful.delay <= (CURRENT_DATE - COALESCE(aml.date_maturity, aml.date))::int
                AND ful.company_id = %(company_id)s
          WHERE account.deprecated IS NOT TRUE
            AND account.account_type = 'asset_receivable'
            AND aml.parent_state = 'posted'
            AND aml.reconciled IS NOT TRUE
            AND aml.blocked IS FALSE
            AND aml.company_id = %(company_id)s
            {"" if partner_ids is None else "AND aml.partner_id IN %(partner_ids)s"}
       GROUP BY partner.id
           ) partner
                      
           --Map the dynamic follow-up delay to the follow-up line
           LEFT JOIN account_followup_followup_line ful ON ful.delay = partner.followup_delay AND ful.company_id = %(company_id)s
           
           -- Get the followup status data
           LEFT OUTER JOIN LATERAL (
               SELECT line.id
                 FROM account_move_line line
                 JOIN account_account account ON line.account_id = account.id
                WHERE line.partner_id = partner.id
                  AND account.account_type = 'asset_receivable'
                  AND account.deprecated IS NOT TRUE
                  AND line.parent_state = 'posted'
                  AND line.reconciled IS NOT TRUE
                  AND line.balance > 0
                  AND line.blocked IS FALSE
                  AND line.company_id = %(company_id)s
                  AND (CURRENT_DATE - COALESCE(line.date_maturity, line.date))::int >= ful.delay
                LIMIT 1
           ) in_need_of_action_aml ON true
           LEFT OUTER JOIN LATERAL (
               SELECT line.id
                 FROM account_move_line line
                 JOIN account_account account ON line.account_id = account.id
                WHERE line.partner_id = partner.id
                  AND account.account_type = 'asset_receivable'
                  AND account.deprecated IS NOT TRUE
                  AND line.parent_state = 'posted'
                  AND line.reconciled IS NOT TRUE
                  AND line.balance > 0
                  AND line.blocked IS FALSE
                  AND line.company_id = %(company_id)s
                  AND COALESCE(line.date_maturity, line.date) < %(current_date)s
                LIMIT 1
           ) exceeded_unreconciled_aml ON true
           LEFT OUTER JOIN ir_property prop_date ON prop_date.res_id = CONCAT('res.partner,', partner.id)
                                                AND prop_date.name = 'followup_next_action_date'
                                                AND prop_date.company_id = %(company_id)s
       """, {
            'company_id': self.env.company.id,
            'partner_ids': tuple(partner_ids or []),
            'current_date': fields.Date.context_today(self),
        }



