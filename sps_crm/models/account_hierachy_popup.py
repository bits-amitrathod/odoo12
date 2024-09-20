from odoo import api, fields, models,_
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc
from werkzeug import urls
import logging


_logger = logging.getLogger(__name__)


class AccountHierarchyReport(models.TransientModel):
    _name = 'popup.account.hierarchy.report'
    _description = "Account Hierarchy Report"

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


        web_base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        self.env['ir.config_parameter'].set_param('web.shopsps_odoo_com', 'https://shopsps.odoo.com')
        matches = ["local", "localhost", "staging", "test", "tes", "bits", "127.0.0.1", "stag"]

        if any([x in web_base_url for x in matches]):
            url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        else:
            url = self.env['ir.config_parameter'].sudo().get_param('web.shopsps_odoo_com')

        flag = True
        current_partner_name = ""
        partner = 0
        data_val = ''
        res_model = 'partner.link.tracker'
        #_logger.info('--------- _compute_account_hierarchy_html  In Account hierarchy code ')

        current_partner_record = self.env['res.partner'].browse(int(self.env.context.get('default_partner_id')))
        if current_partner_record.id is False:
            vals_list = {'partner_id': current_partner_record.id}
            self.env[res_model].create(vals_list)

        parent_parent = current_partner_record.acc_cust_parent if current_partner_record.acc_cust_parent else current_partner_record
        if current_partner_record.acc_cust_parent.id is False:
            vals_list = {'partner_id': parent_parent.id}
            self.env[res_model].create(vals_list)

        grand_parent = parent_parent.acc_cust_parent if parent_parent.acc_cust_parent else parent_parent
        if parent_parent.acc_cust_parent.id is False:
            vals_list = {'partner_id': grand_parent.id}
            self.env[res_model].create(vals_list)

        list_all = {}  # Graph is a dictionary to hold our child-parent relationships.
        list_all_id_names = {}
        partner_tracker_list = self.env['partner.link.tracker'].search([])

        for tracker in partner_tracker_list:
            # list_all set customer parent id as key and list of child ids
            list_all.setdefault(tracker.acc_cust_parent.id, []).append(tracker.partner_id)
            list_all_id_names.setdefault(tracker.partner_id.id, tracker.partner_id.name)

        final_data = []
        final_data_name = []
        level = 0
        final_data, final_data_name = self.set_data(grand_parent, list_all, level, final_data,
                                                    final_data_name)

        data_val = "<table class='o_list_table table table-sm table-hover table-striped o_list_table_ungrouped' " \
                   "style='table-layout: fixed;'><tbody>"
        for x, list_data in enumerate(final_data):
            # p = list_data.lstrip('&nbps; ')
            customer = self.env['res.partner'].sudo().search([('id', '=', final_data_name[x].id)], limit=1)
            l= []
            facility_code = customer.facility_tpcd if customer.facility_tpcd else ""
            facility_name = ""
            if facility_code:
                facility_name = self.get_facility_name(facility_code)
            sale_mngr = self.get_sales_manager(customer).name if self.get_sales_manager(customer) else ""
            purchase_mngr = self.get_purchase_manager(customer).name if self.get_purchase_manager(customer) else ""
            state = customer.state_id.name if customer.state_id else ""

            for a in customer.category_id:
                if a.name in ['Sales Account', 'ACQ Account']:
                    if a.name =="Sales Account":
                        l.append("<span style='color: #f8f9fa;font-size: smaller;background-color:green;border-radius: 10px;;padding-left: 6px;padding-right: 6px;'>"+a.name+"</span>")
                    elif a.name =="ACQ Account":
                        l.append("<span style='color: #f8f9fa;font-size: smaller;background-color:blue;border-radius: 10px;;padding-left: 6px;padding-right: 6px;'>"+a.name+"</span>")

            s1 =(str('' if not l else (*l,))).replace('"', ' ').replace('(', ' ').replace(')', ' ').replace(',', ' ')
            list_data = list_data or '""'

            if customer.id == current_partner_record.id and flag:
                data_val += f"<tr><td class='o_data_cell o_field_cell o_list_char o_readonly_modifier o_required_modifier' style='border-top:1px solid #dee2e6'><b><a style='color:blue !important;' target='_blank' href='{url}/web#id={final_data_name[x].id}&model=res.partner&view_type=form&menu_id=519'>{list_data}</a></b> {s1} | {facility_name} | {purchase_mngr} | {sale_mngr} | {state}</td></tr>"
                flag = False
            else:
                data_val += f"<tr><td class='o_data_cell o_field_cell o_list_char o_readonly_modifier o_required_modifier' style='border-top:1px solid #dee2e6'><a style='color:black !important;' target='_blank' href='{url}/web#id={final_data_name[x].id}&model=res.partner&view_type=form&menu_id=519'>{list_data}</a> {s1} | {facility_name} | {purchase_mngr} | {sale_mngr} | {state}</td></tr>"



        data_val = data_val + '</tbody></table>'
        return data_val

    def get_facility_name(self, facility_code):
        """ This function is added because the facility_tcpd field
            at customer level is giving string as value and not
            object .And this selection field in not in DB .
               """
        switcher = {
            'health_sys': 'Health System',
            'hospital': 'Hospital',
            'surgery_cen': 'Surgery Center',
            'pur_alli': 'Purchasing Alliance',
            'charity': 'Charity',
            'broker': 'Broker',
            'veterinarian': 'Veterinarian',
            'closed': 'Non-Surgery/Closed',
            'wholesale': 'Wholesale',
            'national_acc': 'National Account Target',
            'other': 'Other',
            'closed1':'Closed',
            'no_surgery':'No Surgery',
            'lab/_research_center': 'Lab/ Research Center'
        }

        return switcher.get(facility_code, "nothing")

    def get_sales_manager(self, customer):
        user_name = None
        if customer.account_manager_cust:
            user_name = customer.account_manager_cust
        elif customer.user_id:
            if customer.user_id.name == "National Accounts" and customer.national_account_rep:
                user_name = customer.national_account_rep
            else:
                user_name = customer.user_id
        elif customer.national_account_rep:
            user_name = customer.national_account_rep
        else:
            user_name = customer.user_id
        return user_name
    def get_purchase_manager(self, customer):
       return customer.acq_manager if customer.acq_manager else None

    def set_data(self, partner, list_all, level, final_data, final_data_name):
        # final_data.append(partner.name + '*' + str(partner.id) + '*')
        final_data.append(partner.name)
        final_data_name.append(partner)
        level = level + 1
        if partner.id in list_all and level <= 9:
            partner_child_list = list_all[partner.id]
            for prt in partner_child_list:
                self.recursive_hir(prt, list_all, level, final_data, final_data_name)

        return final_data, final_data_name

    def recursive_hir(self, partner, list_all, level, final_data, final_data_name):
        data_dash = '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ' * level + '&nbsp;'
        # final_data.append(data_dash + '&nbsp;' + partner.name + '*' + str(partner.id) + '*')
        final_data.append(data_dash + '&nbsp;' + partner.name)
        # data_dash = '------ ' * level + '>'
        # final_data.append(data_dash + ' ' + child)
        final_data_name.append(partner)
        level = level + 1
        if partner.id in list_all and level <= 9:
            partner_child_list = list_all[partner.id]
            for prt in partner_child_list:
                self.recursive_hir(prt, list_all, level, final_data, final_data_name)





#
class SalePaymentLink(models.TransientModel):
    _inherit = "payment.link.wizard"
    _description = "Generate Sales Payment Link"

    pass

    # def get_base_url_custom(self):
    #     """
    #     Returns Custom URL as per client requirement
    #     Ticket 659, Added through code , so that even record is deleted it will recreate
    #     """
    #     web_base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
    #     self.env['ir.config_parameter'].sudo().set_param('web.shopsps_com', 'https://www.shopsps.com')
    #     matches = ["local", "localhost", "staging", "test", "tes", "bits", "127.0.0.1", "stag"]
    #
    #     if any([x in web_base_url for x in matches]):
    #         url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
    #     else:
    #         url = self.env['ir.config_parameter'].sudo().get_param('web.shopsps_com')
    #
    #     return url
    #
    # def _generate_link(self):
    #     """ Override of the base method to add the order_id in the link. """
    #     for payment_link in self:
    #         # only add order_id for SOs,
    #         # otherwise the controller might try to link it with an unrelated record
    #         # NOTE: company_id is not necessary here, we have it in order_id
    #         # however, should parsing of the id fail in the controller, let's include
    #         # it anyway
    #         if payment_link.res_model == 'sale.order':
    #             record = self.env[payment_link.res_model].browse(payment_link.res_id)
    #             payment_link.link = ('%s/website_payment/pay?reference=%s&amount=%s&currency_id=%s'
    #                                 '&partner_id=%s&order_id=%s&company_id=%s&access_token=%s') % (
    #                                     self.get_base_url_custom(),
    #                                     urls.url_quote_plus(payment_link.description),
    #                                     payment_link.amount,
    #                                     payment_link.currency_id.id,
    #                                     payment_link.partner_id.id,
    #                                     payment_link.res_id,
    #                                     payment_link.company_id.id,
    #                                     payment_link.access_token
    #                                 )
    #         else:
    #             self._generate_link_invoice_custom()
    #
    # def _generate_link_invoice_custom(self):
    #     for payment_link in self:
    #         record = self.env[payment_link.res_model].browse(payment_link.res_id)
    #         link = ('%s/website_payment/pay?reference=%s&amount=%s&currency_id=%s'
    #                 '&partner_id=%s&access_token=%s') % (
    #                     self.get_base_url_custom(),
    #                     urls.url_quote_plus(payment_link.description),
    #                     payment_link.amount,
    #                     payment_link.currency_id.id,
    #                     payment_link.partner_id.id,
    #                     payment_link.access_token
    #                 )
    #         if payment_link.company_id:
    #             link += '&company_id=%s' % payment_link.company_id.id
    #         if payment_link.res_model == 'account.move':
    #             link += '&invoice_id=%s' % payment_link.res_id
    #         payment_link.link = link