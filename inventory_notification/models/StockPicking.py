from odoo import models, fields, api,_
from odoo.exceptions import UserError, AccessError,ValidationError
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.multi
    def button_validate(self):
        print("Inside Notifiction")
        #result=super(StockPicking,self).button_validate()
        '''print("After Notifiction button validation")
        inv_notification = self.env['inventory.notification.scheduler'].search([])
        inv_notification.pick_notification_for_customer(self)
        print("After shipment_notification_for_user function")'''