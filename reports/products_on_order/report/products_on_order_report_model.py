import logging
from odoo import api, fields, models

log = logging.getLogger(__name__)


class ReportProductsOnOrder(models.AbstractModel):
    _name = 'report.products_on_order.prod_on_order_temp'

    @api.model
    def get_report_values(self, docids, data=None):
        products_on_order_list = self.env['products.on_order'].browse(docids)

        group_by_list = {}
        for products_on_order in products_on_order_list:
            order_line = [products_on_order.order_id.name, products_on_order.partner_id.display_name,
                          products_on_order.qty_ordered, products_on_order.qty_remaining]
            key = ""
            if products_on_order.product_id.product_tmpl_id.sku_code:
                key = str(products_on_order.product_id.product_tmpl_id.sku_code) + str(" - ")
            key = key + str(products_on_order.product_id.product_tmpl_id.name)
            try:
                group_by_list[key].append(order_line)
            except KeyError:
                group_by_list[key] = [order_line]


        final_list = []
        for product_name, line_list in group_by_list.items():
            inner_list = [product_name, line_list]
            remainig_so_qty = 0
            for line in line_list:
                remainig_so_qty = remainig_so_qty + line[3]
            inner_list.append(remainig_so_qty)
            final_list.append(inner_list)

        log.info('final list: %r', final_list)

        datas = {
            'form': final_list,

        }
        action = self.env.ref('products_on_order.action_report_products_on_order').report_action([], data=datas)
        action.update({'target': 'main','data': datas})

        return action


