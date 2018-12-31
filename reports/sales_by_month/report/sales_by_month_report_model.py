import logging
from odoo import api, fields, models
from datetime import datetime

log = logging.getLogger(__name__)


class ReportProductSaleByCount(models.AbstractModel):
    _name = 'report.sales_by_month.sales_by_month_template'

    @api.model
    def get_report_values(self, docids, data=None):

        if len(docids) == 1:
            ids = "(" + str(docids[0]) + ")"
        else:
            ids = str(tuple(docids))
        view='sales_by_month'
        records = "select sbm.sku_code,sbm.p_name,concat(sbm.currency_symbol,' ',cast(sbm.product_price as varchar)) as product_price,sbm.total_sale_quantity, sbm.total_amount," \
                  "concat(sbm.currency_symbol,' ',cast(sbm.total_amount as varchar)) as total_amount,sbm.start_date,sbm.end_date,sbm.currency_symbol  from  " + view +" as sbm where id in "  + ids
        self._cr.execute(records)
        records = self._cr.fetchall()
        for record in records:
            record

        popup = self.env['salesbymonth.popup'].search([('create_uid', '=', self._uid)], limit=1, order="id desc")

        if popup.compute_at_date:
            date = datetime.strptime(popup.start_date, '%Y-%m-%d').strftime('%m/%d/%Y') + " - " + datetime.strptime(
                popup.end_date, '%Y-%m-%d').strftime('%m/%d/%Y')
        else:
            date = False

        return {
            'data': records,
            'date': date}