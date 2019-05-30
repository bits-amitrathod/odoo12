from odoo import models, api,_
import logging

_logger = logging.getLogger(__name__)


class StockBackorder(models.TransientModel):
    _inherit = "stock.backorder.confirmation"

    def process(self):
        action = super(StockBackorder, self).process()

        inv_notification = self.env['inventory.notification.scheduler'].search([])
        for picking in self.pick_ids:
            if picking.sale_id:
                if picking.picking_type_id.name == 'Pick' and picking.state == 'done':
                    inv_notification.pick_notification_for_user(picking)
        return action

    def process_cancel_backorder(self):
        action = super(StockBackorder, self).process_cancel_backorder()

        inv_notification = self.env['inventory.notification.scheduler'].search([])
        for picking in self.pick_ids:
            if picking.sale_id:
                if picking.picking_type_id.name == 'Pick' and picking.state == 'done':
                    inv_notification.pick_notification_for_user(picking)
        return action