import logging
from odoo import api, fields, models

log = logging.getLogger(__name__)


class ReportProductsOnOrder(models.AbstractModel):
    _name = 'report.returned_sales.returned_sales_temp'

    @api.model
    def get_report_values(self, docids, data=None):
        returned_sales_list = self.env['report.returned.sales.order'].browse(docids)

        group_by_list = {}
        for returned_sales in returned_sales_list:
            order_line = [returned_sales.order_id.name, returned_sales.partner_id.display_name,returned_sales.user_id.display_name,
                          returned_sales.done_qty,returned_sales.product_uom_id.name, returned_sales.cost_price]
            key = ""
            if returned_sales.product_id.product_tmpl_id.sku_code:
                key = str(returned_sales.product_id.product_tmpl_id.sku_code) + str(" - ")

            key = key + str(returned_sales.product_id.product_tmpl_id.name)
            try:
                group_by_list[key].append(order_line)
            except KeyError:
                group_by_list[key] = [order_line]


        final_list = []
        for product_name, line_list in group_by_list.items():
            inner_list = [product_name, line_list]
            total_done_qty = 0.0
            total_cost_price = 0.00
            for line in line_list:
                total_done_qty = total_done_qty + line[3]
                total_cost_price = total_cost_price + line[5]
            inner_list.append(total_done_qty)
            inner_list.append(total_cost_price)
            final_list.append(inner_list)

        log.info('final list: %r', final_list)

        datas = {
            'ids': self,
            'form': final_list,

        }
        action = self.env.ref('returned_sales.action_report_returned_sales').report_action([], data=datas)
        action.update({'target': 'main'})

        return action


