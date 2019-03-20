from odoo import api, fields, models
from odoo.osv import osv
import warnings
from odoo import api, fields, models, tools
from odoo.exceptions import UserError, ValidationError
import logging


from odoo import models, fields, api
import datetime
_logger = logging.getLogger(__name__)




class InventoryAvailability(models.Model):
    _inherit="stock.scrap"

class InventoryAvailabilityReport(models.AbstractModel):
    _name = 'report.scrap_report.inventory_scrap_print'

    @api.model
    def get_report_values(self, docids, data=None):
        scrap_products=self.env['stock.scrap'].browse(docids)
        return {'data': scrap_products}


