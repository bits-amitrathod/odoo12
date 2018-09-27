

import time
from odoo import api, fields, models
from odoo.tools import float_repr
from numpy.core.defchararray import upper
from dateutil.parser import parse
from odoo.exceptions import UserError



class ReportProducts(models.AbstractModel):
    _name = 'report.tps_report_sale.report_products'



    @api.model
    def get_report_values(self, docids, data=None):
        purchase_orders = self.env['sale.order'].browse(docids)
        return {
            'doc_ids': data.get('ids'),
            'doc_model': data.get('model'),
            'data': purchase_orders,
        }



