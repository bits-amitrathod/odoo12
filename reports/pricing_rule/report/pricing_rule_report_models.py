from odoo import api, models
import logging
from itertools import groupby

_logger = logging.getLogger(__name__)


class OnHandByDateReportModel(models.AbstractModel):
    _name = 'report.pricing_rule.inv_pricing_rule_template'
    _description = "report Pricing Rule Template"

    @api.model
    def _get_report_values(self, docids, data=None):

        # select = """ SELECT pr.customer_name,pr.product_code,pr.product_name,pr.cost
        #         FROM res_pricing_rule pr
        #          """
        # self._cr.execute(select)
        result = self.env['res.pricing_rule'].browse(docids)
        products=[]
        it = iter(result)
        for product in it:
            products.append([product,next(it,False)])
        return {'pricing_rule_result' :products }


