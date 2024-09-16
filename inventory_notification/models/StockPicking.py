from odoo import models, api,_
import logging
SUPERUSER_ID_INFO = 2

_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
    _inherit = "stock.picking"

    def getParent(self, saleOrder):
        return saleOrder.partner_id.parent_id if saleOrder.partner_id.parent_id else saleOrder.partner_id

    #@api.multi
    def button_validate(self):
        inv_notification = self.env['inventory.notification.scheduler'].search([])
        for picking in self:
            if picking.sale_id and picking.sale_id.team_id and picking.getParent(picking.sale_id).picking_warn in ["block"]:
                return {
                    'name': _("Warning for %s") % picking.getParent(picking.sale_id).name,
                    'view_type': 'form',
                    "view_mode": 'form',
                    'res_model': 'warning.popup.wizard',
                    'type': 'ir.actions.act_window',
                    'context': {'default_picking_warn_msg': picking.getParent(picking.sale_id).picking_warn_msg},
                    'target': 'new', }
            else:
                action = super(StockPicking, self).button_validate()
                if picking.sale_id:
                    _logger.info("***********Pick type and State ****************************")
                    _logger.info(self.picking_type_id.name + "  *********** " + self.state)
                    if self.picking_type_id.name == 'Pick' and self.state == 'done':
                        # inv_notification.pick_notification_for_customer(self)
                        inv_notification.pick_notification_for_user(self)
                        self.email_after_pick_validate()
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

    def email_after_pick_validate(self):
        if self.sale_id:
            if self.sale_id.account_manager and self.sale_id.customer_success:
                am = self.sale_id.account_manager.login if self.sale_id.account_manager.login else None
                cs = self.sale_id.customer_success.login if self.sale_id.customer_success.login else None
                if cs and am:
                    to = f"{am},{cs}"
                    base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                    # base_url = base_url + '/my/orders/' + str(self.sale_id.id)
                    base_url = base_url + '/web#id=' + str(self.sale_id.id) + '&action=315&model=sale.order&view_type=form&cids=1%2C3&menu_id=201'
                    template = self.env.ref("inventory_notification.pick_done_ka_and_cs_email_template")
                    context = {'email_from': 'info@surgicalproductsolutions.com',
                               'email_to': to,
                               'subject': 'Pick Done Internal',
                               'facility_name': self.sale_id.partner_id.display_name,
                               'so_name': self.sale_id.name,
                               'access_url': base_url
                               }
                    template.with_context(context).sudo().send_mail(SUPERUSER_ID_INFO, raise_exception=True)