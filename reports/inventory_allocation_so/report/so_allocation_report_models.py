from odoo import api, models
import logging
from itertools import groupby

_logger = logging.getLogger(__name__)


class OnHandByDateReportModel(models.AbstractModel):
    _name = 'report.inventory_allocation_so.inv_sale_allocation_template'

    @api.model
    def get_report_values(self, docids, data=None):
        if len(docids) == 1:
            ids="("+str(docids[0])+")"
        else:
            ids=tuple(docids)
        select = """ SELECT sale_order_name, 
                concat(so.currency_symbol,' ',sum(so.cost))  as total_cost,
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
                 CASE WHEN so.product_uom_qty IS NULL THEN
                 ''
                 ELSE
                 so.product_uom_qty END
                ,
                CASE WHEN so.cost IS NULL THEN
                 ''
                 ELSE
                 concat(so.currency_symbol,' ',cast(so.cost as varchar)) END
                ]) as type ,
                concat(sum(so.product_quantity),' ', so.product_uom) as total_qty
                FROM inventory_allocation_so so where id in """
        select=select+ ' '+str(ids)+ ' '+""" 
                GROUP BY sale_order_name,currency_symbol,product_uom   """
        self._cr.execute(select)
        result = self.env.cr.fetchall()
        _logger.info("selct :%r", result)
        sale_order_list = []
        for sale_order in result:
            orders = [sale_order[0],sale_order[1], sale_order[2],sale_order[3]]
            sale_order_list.append(orders)

        return {'sale_order_list' :sale_order_list }


