import logging
from odoo import api, fields, models

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
        return {
            'data': records}