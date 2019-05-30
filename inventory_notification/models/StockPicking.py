from odoo import models, api,_
import logging

_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.multi
    def button_validate(self):

        action=super(StockPicking,self).button_validate()

        inv_notification = self.env['inventory.notification.scheduler'].search([])
        for picking in self:
            if picking.sale_id:
                if self.picking_type_id.name=='Pick' and self.state=='done':
                    # inv_notification.pick_notification_for_customer(self)
                    inv_notification.pick_notification_for_user(self)

                elif self.picking_type_id.name=='Pack' or self.picking_type_id.name=='Pull':
                    inv_notification.pull_notification_for_user(self)

                elif self.picking_type_id.name == 'Delivery Orders':
                    inv_notification.out_notification_for_sale(self)
        return action