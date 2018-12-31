from odoo import api, models
from odoo import api, fields, models
import logging


class ReportPurchaseSalespersonWise(models.AbstractModel):
    _name = 'report.aging_report.purchase_report'

    @api.model
    def get_report_values(self, docids, data=None):
        aging_report = self.env['aging.report'].search([('id', 'in', docids)], order='warehouse_id')

        index = ""
        dictionary = {}
        for records in aging_report:
            cols = {'sku': records.sku_code,
                    'product': records.product_name,
                    'lot': records.lot_name,
                    'qty': records.qty,
                    'uom': records.product_uom_id,
                    'cr_date': records.create_date,
                    'exp_date': records.use_date,
                    'days': records.days

                    }

            if index == records.warehouse_id.name :
                dictionary[index].append(cols)
            else:
                index = records.warehouse_id.name
                dictionary[index] = [cols]

        return {'dictionary': dictionary,}

# return {
#    'data': self.env['aging.report'].browse(docids)
# }
