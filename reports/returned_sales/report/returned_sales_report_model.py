import logging
from odoo import api, fields, models

log = logging.getLogger(__name__)


class ReportProductsOnOrder(models.AbstractModel):
    _name = 'report.returned_sales.prod_on_order_temp'

    @api.model
    def get_report_values(self, docids, data=None):
        returned_sales_list = self.env['products.on_order'].browse(docids)

        group_by_list = {}
        for returned_sales in returned_sales_list:
            order_line = [returned_sales.product_id.product_tmpl_id.name, returned_sales.partner_id.display_name,
                          returned_sales.qty_ordered, returned_sales.qty_remaining]
            try:
                group_by_list[returned_sales.name].append(order_line)
            except KeyError:
                group_by_list[returned_sales.name] = [order_line]


        final_list = []
        for order_name, line_list in group_by_list.items():
            inner_list = [order_name, line_list]
            remainig_so_qty = 0
            for line in line_list:
                remainig_so_qty = remainig_so_qty + line[3]
            inner_list.append(remainig_so_qty)
            final_list.append(inner_list)

        log.info('final list: %r', final_list)

        datas = {
            'ids': self,
            'form': final_list,

        }
        action = self.env.ref('returned_sales.action_report_returned_sales').report_action([], data=datas)
        action.update({'target': 'main'})

        return action


