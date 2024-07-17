from odoo import api, models
import logging
from itertools import groupby

_logger = logging.getLogger(__name__)


class OnHandByDateReportModel(models.AbstractModel):
    _name = 'report.margins.margins_temp'
    _description = "OnHand ByDate Report Model"

    @api.model
    def _get_report_values(self, docids, data=None):
        margins_list = self.env['margins'].browse(docids)

        group_by_list = {}
        group_by_product = {}
        insert_date_range = True

        for margins in margins_list:
            if insert_date_range:
                group_by_list.update({'date_from': margins.date_from, 'date_to': margins.date_to, 'items': []})
                insert_date_range = False
            product_name = str(margins.product_id.product_tmpl_id.sku_code) + str(' - ') + str(
                margins.product_id.product_tmpl_id.name)
            inner_list = [margins.order_id.name, margins.unit_cost, margins.qty, margins.unit_price,
                          margins.total_unit_price, margins.total_unit_cost, margins.margin, margins.margin_percentage]
            if product_name in group_by_product:
                group_by_product[product_name].append(inner_list)
            else:
                group_by_product.update({product_name: [inner_list]})

        items = []
        for product_name, products in group_by_product.items():
            sum_of_margins = sum_of_unit_price = sum_of_cogs = sum_of_margins_percentage = 0
            for product in products:
                sum_of_unit_price = sum_of_unit_price + product[4]
                sum_of_cogs = sum_of_cogs + product[5]
                sum_of_margins = sum_of_margins + product[6]
                sum_of_margins_percentage = sum_of_margins_percentage + product[7]
            sum_of_margins_percentage = sum_of_margins_percentage / len(products)
            items.append({'product_name': product_name, 'items': products,
                          'totals': [sum_of_unit_price, sum_of_cogs, sum_of_margins, sum_of_margins_percentage]})

        group_by_list.update({'items': items})

        action = self.env.ref('margins.action_report_margins').report_action([], data=group_by_list)
        action.update({'target': 'main'})

        return action

