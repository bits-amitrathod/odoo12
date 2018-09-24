from odoo import api, fields, models
from odoo.tools import float_repr
from numpy.core.defchararray import upper
#
# class SaleSalespersonReport(models.TransientModel):
#     _name = 'sale.salesperson.report'
#
#     start_date = fields.Date('Start Date', required=True)
#     end_date = fields.Date(string="End Date", required=True)
#     user_ids = fields.Many2many('res.users', string="Salesperson")
#
#     @api.model
#     def check(self, data):
#         if data:
#             return upper(data)
#         else:
#             return " "
#     @api.multi
#     def print_salesperson_vise_report(self):
#         sale_orders = self.env['sale.order'].search([('state', '=', 'sale')])
#         groupby_dict = {}
#         for user in self.user_ids:
#             filtered_order = list(filter(lambda x: x.user_id == user, sale_orders))
#             filtered_by_date = list(
#                 filter(lambda x: x.date_order >= self.start_date and x.date_order <= self.end_date, filtered_order))
#             groupby_dict[user.name] = filtered_by_date
#         final_list = []
#         for user in groupby_dict.keys():
#             temp = []
#             list1 = []
#             for order in groupby_dict[user]:
#                 temp_2 = []
#                 temp_2.append(order.name)
#                 temp_2.append(fields.Datetime.from_string(str(order.date_order)).date().strftime('%m/%d/%Y'))
#                 temp_2.append(float_repr(order.amount_total,precision_digits=2))
#                 temp.append(temp_2)
#             list1.append(user)
#             list1.append(sorted(temp, key=lambda x: x[0], reverse=False))
#             final_list.append(list1)
#         final_list.sort(key=lambda x: self.check(x[0]))
#         print(final_list)
#
#         datas = {
#             'ids': self,
#             'model': 'sale.salesperson.report',
#             'form': final_list,
#             'start_date': fields.Datetime.from_string(str(self.start_date)).date().strftime('%m/%d/%Y'),
#             'end_date': fields.Datetime.from_string(str(self.end_date)).date().strftime('%m/%d/%Y'),
#         }
#         action = self.env.ref('sr_sales_report_saleperson_groupby.action_report_sales_saleperson_wise').report_action([],
#                                                                                                                     data=datas)
#         action.update({'target': 'main'})
#         return action

