from odoo import api, models
from odoo import api, fields, models
import logging


class ReportPurchaseSalespersonWise(models.AbstractModel):
    _name = 'report.aging_report.purchase_report'
    _description = "Report Purchase Salesperson Wise"

    @api.model
    def _get_report_values(self, docids, data=None):
        aging_report = self.env['aging.report'].search([('id', 'in', docids)], order='warehouse_id')

        warehouse=''
        receving=[]
        shipping=[]
        stock=[]
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
                if records.type == 'Stock':
                    stock.append(cols)
                elif records.type == 'Shipping':
                    shipping.append(cols)
                else:
                    receving.append(cols)
                warehouse = records.warehouse_id.name


        return {'warehouse': warehouse,'receving':receving,'shipping':shipping,'stock':stock}

# return {
#    'data': self.env['aging.report'].browse(docids)
# }
