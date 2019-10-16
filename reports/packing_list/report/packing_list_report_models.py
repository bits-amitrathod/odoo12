from odoo import api, models
import logging
from itertools import groupby

_logger = logging.getLogger(__name__)


class OnHandByDateReportModel(models.AbstractModel):
    _name = 'report.packing_list.sale_packing_list_template'

    @api.model
    def _get_report_values(self, docids, data=None):

        # select = """ SELECT pr.customer_name,pr.product_code,pr.product_name,pr.cost
        #         FROM res_pricing_rule pr
        #          """
        # self._cr.execute(select)
        if len(docids) == 1:
            picking = self.env['stock.picking'].search([('id', 'in', docids)])
            stock_picking_type = self.env['stock.picking.type'].search([('name', '=', 'Delivery Orders')])
            stock_out = self.env['stock.picking'].search([('sale_id', '=', picking.sale_id.id), ('picking_type_id', '=', stock_picking_type.id)])
            result = self.env['stock.picking'].search([('id', 'in', stock_out.ids), ('state', 'not in', ['cancel'])])
        else:
            result = self.env['stock.picking'].search([('id', 'in', docids), ('state', 'not in', ['cancel'])])

        # products=[]
        # it = iter(result)
        # for product in it:
        #     products.append([product,next(it,False)])
        return {'packing_list_result' :result }


