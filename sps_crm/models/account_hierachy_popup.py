from odoo import api, fields, models,_
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc


class AccountHierarchyReport(models.TransientModel):
    _name = 'popup.account.hierarchy.report'

    start_date = fields.Date('Start Date', default=fields.date.today(), required=True,
                             help="Choose a date to get the New Account Bonus Report at that Start date")

    business_development = fields.Many2one('res.users', string="Business Development", index=True,
                                           domain="['|', ('active', '=', True), ('active', '=', False)]")

    key_account = fields.Many2one('res.users', string="Key Account", index=True,
                                  domain="['|', ('active', '=', True), ('active', '=', False)]")

    account_hierarchy_html = fields.Html(compute='_compute_account_hierarchy_html')

    # @api.multi
    def open_table(self):
        start_date = self.string_to_date(str(self.start_date))
        end_date = start_date - datetime.timedelta(days=365)
        end_date_13 = start_date - datetime.timedelta(days=396)
        end_date_13_12months = end_date_13 + datetime.timedelta(days=365)

        tree_view_id = self.env.ref('sps_crm.account_hierarchy_report_list_view').id
        form_view_id = self.env.ref('sps_crm.account_hierarchy_report_form_view').id
        res_model = 'account.hierarchy.report'
        margins_context = {'start_date': start_date, 'end_date': end_date, 'end_date_13': end_date_13,
                           'end_date_13_12months': end_date_13_12months
                           }
        self.env[res_model].with_context(margins_context).delete_and_create()
        action = {
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'view_mode': 'tree',
            'name': 'Account Hierarchy Report',
            'res_model': res_model,
            'context': {'group_by': 'customer'},
        }

        return action

    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(date_string, DEFAULT_SERVER_DATE_FORMAT).date()

    @api.onchange('account_hierarchy_html')
    def _compute_account_hierarchy_html(self):

        current_partner = self.env.context.get('default_partner_id')
        data_val = ''

        query = '''
            WITH RECURSIVE tree_view AS (
                SELECT
                     partner_link_tracker.acc_cust_parent,
                     partner_link_tracker.partner_id,
                     res_partner.name,
                     0 AS level,
                     CAST(partner_link_tracker.id AS varchar(50)) AS order_sequence
                FROM partner_link_tracker join res_partner on res_partner.id = partner_link_tracker.partner_id
                and partner_link_tracker.partner_id = ''' + str(current_partner) + '''

            UNION ALL

                SELECT
                     parent.acc_cust_parent,
                     parent.partner_id,
                     res_partner.name,
                     level + 1 AS level,
                     CAST(order_sequence || '_' || CAST(parent.partner_id AS VARCHAR (50)) AS VARCHAR(50)) AS order_sequence
                FROM partner_link_tracker parent  join res_partner on res_partner.id = parent.partner_id
                JOIN tree_view tv
                  ON parent.acc_cust_parent = tv.partner_id and level < 10
            )

            SELECT
               RIGHT('------------------------------------------> ',level*6) || name
                 AS parent_child_tree , partner_id
            FROM tree_view
            ORDER BY order_sequence;
            '''
        self.env.cr.execute(query)
        new_list = self.env.cr.dictfetchall()
        url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        # http://localhost:8070/web#id=47182&model=res.partner&view_type=form&cids=1&menu_id=519
        data_val = "<table class='o_list_table table table-sm table-hover table-striped o_list_table_ungrouped' " \
                   "style='table-layout: fixed;'><tbody>"
        for list_data in new_list:
            data_val = data_val + "<tr><td class='o_data_cell o_field_cell o_list_char" \
                                  " o_readonly_modifier o_required_modifier' style='border-top:1px solid #dee2e6'>   " \
                                  " <a style='color:black !important;' target='_blank' href=' "+url+'/web#id='+str(list_data['partner_id'])+"&model=res.partner&view_type=form&menu_id=519'>  " \
                       + list_data['parent_child_tree'] + "</a></td></tr>"

        data_val = data_val + '</tbody></table>'
        self.account_hierarchy_html = data_val
