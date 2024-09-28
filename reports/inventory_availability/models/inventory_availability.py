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
    _inherit="product.product"

class InventoryAvailabilityReport(models.AbstractModel):
    _name = 'report.inventory_availability.inventory_availability_print'
    _description = "Inventory Availability Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        products=self.env['product.product'].browse(docids)
        return {'data': products}


