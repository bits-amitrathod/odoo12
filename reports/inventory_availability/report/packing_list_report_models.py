from odoo import api, models
import logging
from itertools import groupby

_logger = logging.getLogger(__name__)


class OnHandByDateReportModel(models.AbstractModel):
    _name = 'report.packing_list.sale_packing_list_template'
    _description = "OnHand By Date Report Model"

    @api.model
    def _get_report_values(self, docids, data=None):

        # select = """ SELECT pr.customer_name,pr.product_code,pr.product_name,pr.cost
        #         FROM res_pricing_rule pr
        #          """
        # self._cr.execute(select)
        result = self.env['res.stock_packing_list'].browse(docids)
        picking = self.env['stock.picking'].search([('id','=',28)])
        _logger.info("picking:%r",picking)
        for sale in result:
            _logger.info("stock.picking: %r",sale)
        # products=[]
        # it = iter(result)
        # for product in it:
        #     products.append([product,next(it,False)])
        return {'packing_list_result' :result }


