from odoo import api, fields, models


class SaleSalespersonReport(models.TransientModel):
    _name = 'report.report_group_by_saleperson.saleperson_temp'
    _description = "Report Sale Salesperson Report"

    @api.model
    def check(self, data):
        if data:
            return data.upper()
        else:
            return " "

    #@api.multi
    def _get_report_values(self, docids, data):
        sale_orders = self.env['sale.order'].search([('state', '=', 'sale'), ('id', 'in', docids)])

        groupby_dict = {}
        old = ""
        for sale_order in sale_orders:

            if old == sale_order.user_id.name:
                groupby_dict[old].append(sale_order)
            else:
                old = sale_order.user_id.name
                groupby_dict[old] = [sale_order]

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

        popup = self.env['popup.gross.sales.by.person'].search([('create_uid', '=', self._uid)], limit=1,
                                                                            order="id desc")


        action = {
            'target': 'main',
            'data': datas,
            'popup': popup
        }

        return action