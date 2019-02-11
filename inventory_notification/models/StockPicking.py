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
        #print("Inside Notifiction")
        super(StockPicking,self).button_validate()
        #print(self.move_type)
        #print(self.picking_type_id.name)
        #print("After Notifiction button validation")
        inv_notification = self.env['inventory.notification.scheduler'].search([])
        if self.picking_type_id.name=='Pick':
            inv_notification.pick_notification_for_customer(self)
            inv_notification.pick_notification_for_user(self)
        elif self.picking_type_id.name=='Pack' or self.picking_type_id.name=='Pull':
            inv_notification.pull_notification_for_user(self)
            #print("Pull notification for inventory manager")
        elif self.picking_type_id.name == 'Delivery Orders':
            inv_notification.out_notification_for_sale(self)
            #print("After shipment_notification_for_user function")



