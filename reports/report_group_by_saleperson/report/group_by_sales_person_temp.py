from odoo import api, fields, models


class SaleSalespersonReport(models.TransientModel):
    _name = 'report.report_group_by_saleperson.saleperson_temp'

    @api.model
    def check(self, data):
        if data:
            return data.upper()
        else:
            return " "

    @api.multi
    def get_report_values(self, docids, data):
        sale_orders = self.env['sale.order'].search([('state', '=', 'sale'),('id', 'in', docids)])

        groupby_dict = {}
        old=""
        for sale_order in sale_orders:

            if old == sale_order.user_id.name:
                groupby_dict[old].append(sale_order)
            else:
                old = sale_order.user_id.name
                groupby_dict[old] = [sale_order]

        # user_ids = self.env['res.users'].search([('id', 'in', docids)])

        # for user in user_ids:
        #     filtered_order = list(filter(lambda x: x.user_id.id == user.id, sale_orders))
        #     filtered_by_date = filtered_order
        #     groupby_dict[user.name] = filtered_by_date
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

        datas = {
            'ids': self,
            'model': 'sale.order',
            'form': final_list,

        }

        action = {'target': 'main', 'data': datas}
        return action
