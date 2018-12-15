

from odoo import api, fields, models


class SaleSalespersonReport(models.TransientModel):
    _name = 'sale.purchase.history.report'

    start_date = fields.Date('Start Date', required=True)
    end_date = fields.Date(string="End Date", required=True)
    product_id = fields.Many2many('product.product', string="Products")

    @api.multi
    def print_purchase_history_vise_report(self):
        filter = [('date_order', '>=', self.start_date), ('date_order', '<=', self.end_date)]

        if hasattr(self.product_id, 'ids') and len(self.product_id.ids):
            filter.append(('order_line.product_id', 'in', self.product_id.ids))

        sale_orders = self.env['sale.order'].search(filter)

        groupby_dict = {'data': sale_orders}

        final_dict = {}
        for user in groupby_dict.keys():
            temp = []
            for order in groupby_dict[user]:
                temp_2 = []
                temp_2.append(order.name)
                temp_2.append(order.date_order)
                temp_2.append(order.amount_total)
                sum = 0
                for r in order.order_line:
                    sum = sum + r.qty_delivered
                temp_2.append(sum)
                temp_2.append(order.product_id.name)
                temp.append(temp_2)
            final_dict[user] = temp
        datas = {
            'ids': self,
            'model': 'sale.product.report',
            'form': final_dict,
            'start_date': self.start_date,
            'end_date': self.end_date,

        }
        return self.env.ref('sales_purchase_history_report.action_report_purchase_history_wise').report_action([],
                                                                                                               data=datas)
