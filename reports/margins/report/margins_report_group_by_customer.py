from odoo import api, models
import logging
from itertools import groupby

_logger = logging.getLogger(__name__)


class MarginsRerpotGroupByCustomer(models.AbstractModel):
    _name = 'report.margins.margins_group_by_cust_temp'
    _description = "Margins Rerpot GroupBy Customer"

    @api.model
    def _get_report_values(self, docids, data=None):
        margins_list = self.env['margins.group_by_cust'].browse(docids)

        final_list = []
        y_list = []
        z_list = {}

        product_names = customer_names = {}
        date_range = False
        for margins in margins_list:
            if not date_range:
                date_from = margins.date_from
                date_to = margins.date_to
            product_name = str(
                margins.product_id.product_tmpl_id.sku_code) + " - " + margins.product_id.product_tmpl_id.name
            customer_name = str(
                margins.partner_id.id) + " - " + margins.partner_id.display_name

            x_list = [margins.order_id.name, margins.unit_cost, margins.qty,
                      margins.unit_price,
                      margins.total_unit_price, margins.total_unit_cost, margins.margin, margins.margin_percentage]

            y_list.append((margins.id, margins.product_id.id, margins.partner_id.id))

            z_list.update({margins.id: x_list})

            customer_names.update({margins.partner_id.id: customer_name})
            product_names.update({margins.product_id.id: product_name})

        for customer_id, group in groupby(y_list, lambda x: x[2]):
            customer_name = customer_names.get(customer_id)
            customer_dictionary = self._get_customer_dictionary(customer_name, final_list)
            if customer_dictionary is None:
                customer_dictionary = {'customer_name': customer_name, 'products': []}
            for custom_triple in list(group):
                product_name = product_names.get(custom_triple[1])
                product_dictionary = self._get_product_dictionary(product_name, customer_dictionary['products'])
                if product_dictionary is None:
                    customer_dictionary['products'].append(
                        {'product_name': product_name, 'items': [z_list.get(custom_triple[0])]})
                else:
                    product_dictionary['items'].append(z_list.get(custom_triple[0]))
            final_list.append(customer_dictionary)

        # _logger.info('final list: %r', final_list)

        action = self.env.ref('margins.action_report_margins_group_by_customer').report_action([], data={
            'date_from': date_from,
            'date_to': date_to,
            'items': final_list
            })
        action.update({'target': 'main'})

        return action


    def _get_customer_dictionary(self,customer_name, final_list):
        for item in final_list:
            if item['customer_name'] == customer_name:
                return item
        return None

    def _get_product_dictionary(self, product_name, final_list):
        for item in final_list:
            if item['product_name'] == product_name:
                return item
        return None