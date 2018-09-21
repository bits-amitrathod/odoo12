
import logging
from odoo import api, fields, models
from odoo.tools import float_repr
from numpy.core.defchararray import upper
import datetime

log = logging.getLogger(__name__)


class Discount():
    sale_order = ''
    customer = ''
    confirmation_date = 0
    amount = 0
    discount_amount = 0
    total_amount = 0

    @api.model
    def check(self, data):
        if data:
            return upper(data)
        else:
            return " "

    @api.multi
    def addObject(self, filtered_by_current_month):
        dict = {}
        log.info(" inside addObject ")
        for record in filtered_by_current_month:
            object = Discount()
            object.sale_order = record.name
            object.customer = record.partner_id.name
            if record.confirmation_date:
                object.confirmation_date = datetime.datetime.strptime(record.confirmation_date, "%Y-%m-%d %H:%M:%S").date().strftime('%m/%d/%Y')
            else:
                object.confirmation_date = record.confirmation_date
            sum=0
            for r1 in record.order_line:
                sum = sum + (r1.product_uom_qty * r1.price_unit)

            object.amount = record.amount_untaxed
            object.discount_amount = float(sum -record.amount_untaxed)
            object.total_amount = record.amount_total
            dict[record.id] = object

        log.info(" return addObject ")
        return dict


class ReportSalesSalespersonWise(models.AbstractModel):
    _name = 'report.report_discount_summary.discountsummary_temp_test'
    @api.model
    def get_report_values(self, docids, data=None):
         return {'data': self.env['sale.order'].browse(docids)}