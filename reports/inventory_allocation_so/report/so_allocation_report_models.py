from odoo import api, models
import logging
from itertools import groupby

_logger = logging.getLogger(__name__)


class OnHandByDateReportModel(models.AbstractModel):
    _name = 'report.inventory_allocation_so.inv_sale_allocation_template'

    @api.model
    def get_report_values(self, docids, data=None):

        select = """ SELECT sale_order_name, 
                concat(sum(so.cost),' ',so.currency_symbol)  as total_cost,
                array_agg(ARRAY[ 
                 CASE WHEN so.product_code IS NULL THEN
                 ''
                 ELSE
                 so.product_code END
                , 
                CASE WHEN so.product_name IS NULL THEN
                 ''
                 ELSE
                 so.product_name END
                ,
                 CASE WHEN so.product_qty IS NULL THEN
                 ''
                 ELSE
                 cast(so.product_qty as varchar) END
                ,
                CASE WHEN so.cost IS NULL THEN
                 ''
                 ELSE
                 concat(cast(so.cost as varchar),' ',so.currency_symbol) END
                ]) as type 
                FROM inventory_allocation_so so
                GROUP BY sale_order_name,currency_symbol   """
        self._cr.execute(select)
        result = self.env.cr.fetchall()
        _logger.info("selct :%r", result)
        sale_order_list = []
        for sale_order in result:
            orders = [sale_order[0],sale_order[1], sale_order[2]]
            sale_order_list.append(orders)

        return {'sale_order_list' :sale_order_list }


