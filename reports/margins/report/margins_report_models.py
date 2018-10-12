from odoo import api, models


class OnHandByDateReportModel(models.AbstractModel):
    _name = 'report.margins.margins_temp'

    @api.model
    def get_report_values(self, docids, data=None):
        margins_list = self.env['margins'].browse(docids)

        group_by_list = {}
        # i = 0
        # total_qty = 0
        # total_assets_value = 0
        # group_by = "product_id"
        # for margins in margins_list:
        #     if not i:
        #         group_by_list.update({'date_range' : margins.date_range})
        #         group_by_list.update({'items' : []})
        #         group_by = margins.group_by
        #
        #
        #     i = i + 1
        #     group_by_list['items'].append([stock.sku_code, stock.product_id.product_tmpl_id.name, stock.vendor_name,
        #                                    stock.qty_on_hand, stock.unit_price, stock.assets_value, stock.vendor_name])
        #     total_qty = total_qty + stock.qty_on_hand
        #     total_assets_value = total_assets_value + stock.assets_value
        #
        # group_by_list.update({'total_qty': total_qty})
        #
        # group_by_list.update({'total_assets_value': total_assets_value})
        #
        # group_by_list.update({'show_cost': show_cost})

        action = self.env.ref('on_hand_by_date.action_report_on_hand_by_date').report_action([], data=group_by_list)
        action.update({'target': 'main'})

        return action