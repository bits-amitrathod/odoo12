from odoo import models, api,_
import logging

_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
    _inherit = "stock.picking"

    #@api.multi
    def button_validate(self):
        inv_notification = self.env['inventory.notification.scheduler'].search([])
        for picking in self:
            if picking.sale_id and picking.sale_id.team_id and picking.sale_id.team_id.name in ["Website",
                                                                                    "My In-Stock Report"] and picking.partner_id.picking_warn in ["block"]:
                return {
                    'name': _("Warning for %s") % picking.partner_id.name,
                    'view_type': 'form',
                    "view_mode": 'form',
                    'res_model': 'warning.popup.wizard',
                    'type': 'ir.actions.act_window',
                    'context': {'default_picking_warn_msg': picking.partner_id.picking_warn_msg},
                    'target': 'new', }
            else:
                action = super(StockPicking, self).button_validate()
                if picking.sale_id:
                    _logger.info("***********Pick type and State ****************************")
                    _logger.info(self.picking_type_id.name + "  *********** " + self.state)
                    if self.picking_type_id.name == 'Pick' and self.state == 'done':
                        # inv_notification.pick_notification_for_customer(self)
                        inv_notification.pick_notification_for_user(self)
                    elif self.picking_type_id.name == 'Pack' or self.picking_type_id.name == 'Pull' and self.state == 'done':
                        inv_notification.pull_notification_for_user(self)
                    elif self.picking_type_id.name == 'Delivery Orders' and self.state == 'done':
                        _logger.info(" Delivery Orders ******** Start********")
                        _logger.info(" Delivery Orders ******** Delivery Done ***** Start********")
                        inv_notification.out_notification_for_sale(self)
                        _logger.info(" Delivery Orders ******** Delivery Done ***** End********")
                        _logger.info(" Delivery Orders ********low Stock ***** Start ********")
                        product_ids = self.unique(self.env['stock.move.line'].search([('picking_id', '=', self.id)]))
                        # inv_notification.process_notify_low_stock_products(product_ids)
                        _logger.info(" Delivery Orders ********low Stock ***** End ********")
                        _logger.info(" Delivery Orders ************* End********")
                # elif picking.purchase_id:
                #     if self.picking_type_id.name == 'Receipts' and self.state == 'done':
                #         inv_notification.po_receive_notification_for_acquisitions_manager(self)
                return action

    def unique(self,list1):
        # intilize a null list
        unique_list = []
        # traverse for all elements
        for x in list1:
            # check if exists in unique_list or not
            if x.product_id not in unique_list:
                unique_list.append(x.product_id)
        return unique_list