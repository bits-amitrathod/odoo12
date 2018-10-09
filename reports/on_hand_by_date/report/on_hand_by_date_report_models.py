from odoo import api, models


class OnHandByDateReportModel(models.AbstractModel):
    _name = 'report.on_hand_by_date.on_hand_by_date_temp'

    @api.model
    def get_report_values(self, docids, data=None):
        on_hand_by_date_stock_list = self.env['on_hand_by_date.stock'].browse(docids)

        group_by_list = {}
        i = 0
        for stock in on_hand_by_date_stock_list:
            if not i:
                group_by_list.update({'report_date' : stock.report_date})
                group_by_list.update({'items' : []})
            i = i + 1
            group_by_list['items'].append([stock.sku_code, stock.product_id.product_tmpl_id.name, stock.vendor_name,
                                           stock.qty_on_hand, stock.unit_price, stock.assets_value, stock.vendor_name])



        datas = {
            'form': group_by_list,
        }
        action = self.env.ref('on_hand_by_date.action_report_on_hand_by_date').report_action([], data=group_by_list)
        action.update({'target': 'main'})

        return action