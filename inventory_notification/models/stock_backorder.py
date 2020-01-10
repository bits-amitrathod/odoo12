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

                elif picking.picking_type_id.name=='Pack' or picking.picking_type_id.name=='Pull' and picking.state=='done':
                    inv_notification.pull_notification_for_user(picking)

                elif picking.picking_type_id.name == 'Delivery Orders' and picking.state=='done':
                    _logger.info(" Delivery Orders ******** backorder ***** Start********")
                    inv_notification.out_notification_for_sale(picking)
                    _logger.info(" Delivery Orders ********low Stock ***** Start ********")
                    product_ids = self.unique(self.env['stock.move.line'].search([('picking_id', '=', picking.id)]))
                    inv_notification.process_notify_low_stock_products(product_ids)
                    _logger.info(" Delivery Orders ********low Stock ***** End ********")
                    _logger.info(" Delivery Orders ******** backorder ***** End ********")

                # Note Section code
                if picking.picking_type_id.name == "Pick" and picking.state == "done":
                    picking.note_readonly_flag = 1
                    picking.add_note_in_log_section()
                    for picking_id in picking.sale_id.picking_ids:
                        if picking_id.state != 'cancel' and picking_id.picking_type_id.name == 'Pull' and picking_id.state == 'assigned':
                            picking_id.note = picking.note
                elif picking.picking_type_id.name == "Pull" and picking.state == "done":
                    picking.note_readonly_flag = 1
                    picking.add_note_in_log_section()
                    for picking_id in picking.sale_id.picking_ids:
                        if picking_id.state != 'cancel' and picking_id.picking_type_id.name == 'Delivery Orders' and picking_id.state == 'assigned':
                            picking_id.note = picking.note
                elif picking.picking_type_id.name == "Delivery Orders" and picking.state == "done":
                    picking.note_readonly_flag = 1
                    picking.add_note_in_log_section()

            # elif picking.purchase_id:
            #     if picking.picking_type_id.name == 'Receipts' and  picking.state == 'done':
            #         inv_notification.po_receive_notification_for_acquisitions_manager(picking)

        return action

    def process_cancel_backorder(self):
        action = super(StockBackorder, self).process_cancel_backorder()

        inv_notification = self.env['inventory.notification.scheduler'].search([])
        for picking in self.pick_ids:
            if picking.sale_id:
                if picking.picking_type_id.name == 'Pick' and picking.state == 'done':
                    inv_notification.pick_notification_for_user(picking)

                elif picking.picking_type_id.name=='Pack' or picking.picking_type_id.name=='Pull' and picking.state=='done':
                    inv_notification.pull_notification_for_user(picking)

                elif picking.picking_type_id.name == 'Delivery Orders' and picking.state=='done':
                    _logger.info(" Delivery Orders ******** cancel_backorder ***** Start********")
                    inv_notification.out_notification_for_sale(picking)
                    _logger.info(" Delivery Orders ********low Stock ***** Start ********")
                    product_ids = self.unique(self.env['stock.move.line'].search([('picking_id', '=', picking.id)]))
                    inv_notification.process_notify_low_stock_products(product_ids)
                    _logger.info(" Delivery Orders ********low Stock ***** End ********")
                    _logger.info(" Delivery Orders ******** cancel_backorder ***** End********")
            # elif picking.purchase_id:
            #     if picking.picking_type_id.name == 'Receipts' and  picking.state == 'done':
            #         inv_notification.po_receive_notification_for_acquisitions_manager(picking)
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