
import logging
from odoo import api, fields, models
from odoo.tools import float_repr
from numpy.core.defchararray import upper
import datetime

class ReportSalesSalespersonWise(models.AbstractModel):
    _name = 'report.report_discount_summary.discountsummary_temp_test'
    @api.model
    def get_report_values(self, docids, data=None):
         return {'data': self.env['sale.order'].browse(docids)}