from odoo import api, fields, models,_
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc
import logging

_logger = logging.getLogger(__name__)


class AccountHierarchyReport(models.TransientModel):
    _name = 'popup.account.hierarchy.report'

    start_date = fields.Date('Start Date', default=fields.date.today(), required=True,
                             help="Choose a date to get the New Account Bonus Report at that Start date")

    business_development = fields.Many2one('res.users', string="Business Development", index=True,
                                           domain="['|', ('active', '=', True), ('active', '=', False)]")

    key_account = fields.Many2one('res.users', string="Key Account", index=True,
                                  domain="['|', ('active', '=', True), ('active', '=', False)]")

    account_hierarchy_html = fields.Html(store=False, readonly=True)

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

    def _compute_account_hierarchy_html(self):

        partner = 0
        data_val = ''
        _logger.info('--------- _compute_account_hierarchy_html  In Account hierarchy code ')

        current_partner = self.env.context.get('default_partner_id')
        current_partner_record = self.env['partner.link.tracker'].search([('partner_id', '=', current_partner)],
                                                                         limit=1)
        res_model = 'partner.link.tracker'
        partner = current_partner

        if current_partner_record.partner_id.id is False:
            vals_list = {'partner_id': partner}
            parent_partner = self.env[res_model].create(vals_list)

        if current_partner_record.acc_cust_parent.id:
            partner = current_partner_record.acc_cust_parent.id

        parent_partner = self.env['partner.link.tracker'].search([('partner_id', '=', partner)], limit=1)
        if parent_partner.partner_id.id is False:
            vals_list = {'partner_id': partner}
            parent_partner = self.env[res_model].create(vals_list)

        if parent_partner.acc_cust_parent.id:
            partner = parent_partner.acc_cust_parent.id

        grand_parent_partner = self.env['partner.link.tracker'].search([('partner_id', '=', partner)], limit=1)
        if grand_parent_partner.partner_id.id is False:
            vals_list1 = {'partner_id': partner}
            parent_partner = self.env[res_model].create(vals_list1)

        list_all = {}  # Graph is a dictionary to hold our child-parent relationships.
        list_all_id_names = {}
        partner_tracker_list = self.env['partner.link.tracker'].search([])
        for tracker in partner_tracker_list:
            list_all.setdefault(tracker.acc_cust_parent.name, []).append(tracker.partner_id.name)
            list_all_id_names.setdefault(tracker.partner_id.name, tracker.partner_id.id)

        final_data = []
        final_data_name = []
        level = 0
        final_data, final_data_name = self.set_data(grand_parent_partner.partner_id.name, list_all, level, final_data,
                                                    final_data_name)

        url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        data_val = "<table class='o_list_table table table-sm table-hover table-striped o_list_table_ungrouped' " \
                   "style='table-layout: fixed;'><tbody>"
        for x, list_data in enumerate(final_data):
            # data_val = data_val + "<tr><td class='o_data_cell o_field_cell o_list_char" \
            #                       " o_readonly_modifier o_required_modifier' style='border-top:1px solid #dee2e6'>" \
            #                       "<a style='color:black !important;' target='_blank' href=' "+url+'/web#id='+str(list_all_id_names[final_data_name[x]])+"&model=res.partner&view_type=form&menu_id=519'>   " \
            #                       " " + list_data + "</a></td></tr>"
            data_val = data_val + "<tr><td class='o_data_cell o_field_cell o_list_char" \
                                  " o_readonly_modifier o_required_modifier' style='border-top:1px solid #dee2e6'>" \
                                  "" + list_data + "</td></tr>"

        data_val = data_val + '</tbody></table>'
        # self.account_hierarchy_html = data_val
        return data_val

    def set_data(self, child, list_all, level, final_data, final_data_name):
        final_data.append(child)
        final_data_name.append(child)
        level = level + 1
        if child in list_all and level <= 9:
            child_list = list_all[child]
            for child in child_list:
                self.recursive_hir(child, list_all, level, final_data, final_data_name)

        return final_data, final_data_name

    def recursive_hir(self, child, list_all, level, final_data, final_data_name):
        data_dash = '------ ' * level + '>'
        final_data.append(data_dash + ' ' + child)
        final_data_name.append(child)
        level = level + 1
        if child in list_all and level <= 9:
            child_list = list_all[child]
            for child in child_list:
                self.recursive_hir(child, list_all, level, final_data, final_data_name)
