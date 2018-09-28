from odoo import api, fields, models
from odoo.tools import float_repr
from numpy.core.defchararray import upper

class SaleSalespersonReport(models.TransientModel):
    _name = 'report.report_group_by_saleperson.saleperson_temp'

    @api.model
    def check(self, data):
        if data:
            return upper(data)
        else:
            return " "

    @api.multi
    def get_report_values(self, docids, data):
        sale_orders = self.env['sale.order'].search([('state', '=', 'sale')])
        user_ids = self.env['res.users'].search([])
        groupby_dict = {}
        for user in user_ids:
            filtered_order = list(filter(lambda x: x.user_id.id == user.id, sale_orders))
            filtered_by_date =  filtered_order
            groupby_dict[user.name] = filtered_by_date
        final_list = []
        currency_id = 0
        for user in groupby_dict.keys():
            temp = []
            list1 = []
            for order in groupby_dict[user]:
                temp_2 = []
                temp_2.append(order.name)
                temp_2.append(fields.Datetime.from_string(str(order.date_order)).date().strftime('%m/%d/%Y'))
                temp_2.append(order.amount_total)
                temp_2.append(order)
                temp.append(temp_2)
            list1.append(user)
            list1.append(sorted(temp, key=lambda x: x[0], reverse=False))
            final_list.append(list1)
        final_list.sort(key=lambda x: self.check(x[0]))
        print(final_list)

        datas = {
            'ids': self,
            'model': 'sale.order',
            'form': final_list,

        }
        action = self.env.ref('report_group_by_saleperson.action_report_sales_saleperson_wise').report_action([],
                                                                                                                    data=datas)
        action.update({'target': 'main'})
        return action
