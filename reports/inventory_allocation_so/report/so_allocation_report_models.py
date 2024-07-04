from odoo import api, models
import logging
from itertools import groupby

_logger = logging.getLogger(__name__)


class OnHandByDateReportModel(models.AbstractModel):
    _name = 'report.inventory_allocation_so.inv_sale_allocation_template'
    _description =  "On Hand By Date Report Model"

    @api.model
    def _get_report_values(self, docids, data=None):
        sale_line_order={}
        sale_list=[]
        sale_order_list = self.env['inventory.allocation_so'].search([('id', 'in', docids)])
        for sale_order_line in sale_order_list:
            if sale_order_line.sale_order_name in sale_line_order:
                sale_list=list(sale_line_order.get(sale_order_line.sale_order_name))
                sale_list.append(sale_order_line)
                sale_line_order[sale_order_line.sale_order_name]=sale_list
            else:
                sale_line_order[sale_order_line.sale_order_name]=[sale_order_line]


        return {'sale_order_list' :sale_line_order }

