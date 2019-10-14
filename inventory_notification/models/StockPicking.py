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
                print('sales order Delivery Process start')
                if self.picking_type_id.name == 'Pick' and self.state == 'done':
                    # inv_notification.pick_notification_for_customer(self)
                    print('sales order Pick Email Process start')
                    inv_notification.pick_notification_for_user(self)
                    print('sales order Pick Email Process end')


                elif self.picking_type_id.name == 'Pack' or self.picking_type_id.name == 'Pull' and self.state == 'done':
                    print('sales order Pull Email Process start')
                    inv_notification.pull_notification_for_user(self)
                    print('sales order Pull Email Process end')

                elif self.picking_type_id.name == 'Delivery Orders' and self.state == 'done':
                    print('sales order Out Email Process Start')
                    inv_notification.out_notification_for_sale(self)
                    print('sales order Out Email Process End')
                    print('sales order Low Stock Email Process start')
                    product_ids = self.unique(self.env['stock.move.line'].search([('picking_id', '=', self.id)]))
                    inv_notification.process_notify_low_stock_products(product_ids)
                    print('sales order Low Stock Email Process end')
            # elif picking.purchase_id:
            #     if self.picking_type_id.name == 'Receipts' and self.state == 'done':
            #         inv_notification.po_receive_notification_for_acquisitions_manager(self)
            print('sales order Delivery Process end')



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