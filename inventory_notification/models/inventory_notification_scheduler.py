    # -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
from datetime import datetime
from datetime import date, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import time
import operator
import base64

_logger = logging.getLogger(__name__)

# Changes done due to odoo_12
SUPERUSER_ID_INFO = 2


class InventoryNotificationScheduler(models.TransientModel):
    _name = 'inventory.notification.scheduler'

    # warehouse_email = "vasimkhan@benchmarkit.solutions"
    # sales_email = "rohitkabadi@benchmarkit.solutions"
    # acquisitions_email = "ajinkyanimbalkar@benchmarkit.solutions"
    # all_email = "tushargodase@benchmarkit.solutions"
    # appraisal_email = "amitrathod@benchmarkit.solutions"

    warehouse_email = "warehouse@surgicalproductsolutions.com"
    sales_email = "sales@surgicalproductsolutions.com"
    acquisitions_email = "acquisitions@surgicalproductsolutions.com"
    all_email = "sps@surgicalproductsolutions.com"
    appraisal_email = "appraisal@surgicalproductsolutions.com"

    def process_manual_notification_scheduler(self):
        _logger.info("process_manual_notification_scheduler called..")
        self.process_notification_scheduler()

    @api.model
    # @api.multi
    def process_notification_scheduler(self, limit=None):
        _logger.info("process_notification_scheduler called")
        if limit is None:
            limit = 40
        self.process_in_stock_scheduler(limit)

    def pick_notification_for_customer(self, picking):
        Stock_Moves = self.env['stock.move'].search([('picking_id', '=', picking.id)])
        super_user = self.env['res.users'].search([('id', '=', SUPERUSER_ID_INFO), ])
        users = self.env['res.users'].search([('active', '=', True), ('id', '=', picking.sale_id.user_id.id)])
        sales_order = []
        for stock_move in Stock_Moves:
            sale_order = {
                'sales_order': picking.sale_id.name,
                'sku': stock_move.product_id.product_tmpl_id.sku_code,
                'Product': stock_move.product_id.name,
                'qty': stock_move.product_qty
            }
            sales_order.append(sale_order)

        vals = {
            'sale_order_lines': sales_order,
            'subject': "Picking Done For Sale Order # " + picking.sale_id.name,
            'description': "Hi " + picking.sale_id.partner_id.display_name + ",<br/> <br/>Please find detail Of Sale Order: "
                           + picking.sale_id.name,
            'header': ['Catalog number', 'Description', 'Quantity'],
            'columnProps': ['sku', 'Product', 'qty'],
            'closing_content': "Thanks & Regards,  <br/> Warehouse Team	"
        }
        self.process_common_email_notification_template(super_user, users, vals['subject'],
                                                        vals['description'], vals['sale_order_lines'], vals['header'],
                                                        vals['columnProps'], vals['closing_content'], None)

    def pull_notification_for_user(self, picking):
        Stock_Moves = self.env['stock.move'].search([('picking_id', '=', picking.id)])
        super_user = self.env['res.users'].search([('id', '=', SUPERUSER_ID_INFO), ])
        users_sale_person = self.env['res.users'].search(
            [('active', '=', True), ('id', '=', picking.sale_id.user_id.id)])
        users = self.env['res.users'].search([('active', '=', True), ('id', '=', picking.sale_id.order_processor.id)])

        final_user = users if users else users_sale_person if users_sale_person else super_user
        sales_order = []
        for stock_move in Stock_Moves:
            sale_order = {
                'sales_order': picking.sale_id.name,
                'sku': stock_move.product_id.product_tmpl_id.sku_code,
                'Product': stock_move.product_id.name,
                'qty': int(stock_move.product_qty)
            }
            sales_order.append(sale_order)
        vals = {
            'sale_order_lines': sales_order,
            'subject': "Pull Done For Sale Order # " + picking.sale_id.name,
            'header': ['Catalog number', 'Description', 'Quantity'],
            'columnProps': ['sku', 'Product', 'qty'],
            'closing_content': 'Thanks & Regards,<br/> Warehouse Team',
            'description': "Hi " + final_user.display_name +
                           ", <br/><br/> Please find detail Of Sale Order: " + picking.sale_id.name + "<br/><br/>" +
                           "<strong> Notes :  </strong>" + (picking.note or "N/A") + "",
        }
        # < strong > Notes: < / strong > " + (str(picking.sale_id.sale_note) if picking.sale_id.sale_note else "
        # N / A
        # ")
        '''vals['description'] = "Hi " + picking.sale_id.user_id.display_name + \
                              ", <br/><br/> Please find detail Of Sale Order: " + picking.sale_id.name+ "<br/>"+\
                             '''

        self.process_common_email_notification_template(super_user, final_user, vals['subject'], vals['description'],
                                                        vals['sale_order_lines'], vals['header'],
                                                        vals['columnProps'], vals['closing_content'])

    def pick_notification_for_user(self, picking):
        Stock_Moves_list = self.env['stock.move'].search([('picking_id', '=', picking.id)])
        Stock_Moves_line = []
        for stock_move in Stock_Moves_list:
            temp = self.env['stock.move.line'].search([('move_id', '=', stock_move.id)])
            Stock_Moves_line.append(temp)
        super_user = self.env['res.users'].search([('id', '=', SUPERUSER_ID_INFO), ])
        users = self.env['res.users'].search([('active', '=', True), ('id', '=', picking.sale_id.user_id.id)])
        sales_order = []
        for stock_move_line in Stock_Moves_line:
            for stock_move_line_single in stock_move_line:
                sale_order = {
                    'sales_order': picking.sale_id.name,
                    'sku': stock_move_line_single.product_id.product_tmpl_id.sku_code,
                    'Product': stock_move_line_single.product_id.name,
                    'qty': int(stock_move_line_single.move_id.product_qty),
                    'lot_name': stock_move_line_single.lot_id.name,
                    'lot_expired_date': stock_move_line_single.lot_id.use_date,
                    'qty_done': int(stock_move_line_single.qty_done),
                    'product_brand_name': stock_move_line_single.product_id.product_brand_id.name
                }
                sales_order.append(sale_order)
        sales_order = sorted(sales_order, key=lambda i: i['product_brand_name'])

        sale_order_ref = picking.sale_id
        address_ref = sale_order_ref.partner_shipping_id
        shipping_adrs = ""
        if address_ref.street:
            shipping_adrs = address_ref.street + '<br/>'
        if address_ref.street2:
            shipping_adrs += address_ref.street2 + '<br/>'
        if address_ref.city:
            shipping_adrs += address_ref.city + '<br/>'
        if address_ref.state_id.name:
            shipping_adrs += address_ref.state_id.name + ', '
        if address_ref.zip:
            shipping_adrs += address_ref.zip + '<br/>'
        if address_ref.country_id.name:
            shipping_adrs += address_ref.country_id.name

        vals = {
            'sale_order_lines': sales_order,
            'subject': "Pick Done For Sale Order # " + picking.sale_id.name,
            'description': "Hi Shipping Team, <br/><br/> " +
                           "<div style=\"text-align: center;width: 100%;\"><strong>The PICK has been completed!</strong></div><br/>" +
                           "<strong> Salesperson: </strong>" + (
                                       sale_order_ref.user_id.partner_id.name or "N/A") + "<br/>" + \
                           "<strong> Order Processor: </strong>" + (
                                       sale_order_ref.order_processor.partner_id.name or "N/A") + "<br/>" + \
                           "<strong> Please proceed with the pulling and shipping of Sales Order: </strong>" + sale_order_ref.name + "<br/>" + \
                           "<strong> Customer PO #:  </strong>" + (sale_order_ref.client_order_ref or "N/A") + "<br/>" + \
                           "<strong> Carrier Info:  </strong>" + (sale_order_ref.carrier_info or "N/A") + "<br/>" + \
                           "<strong> Carrier Account #:  </strong>" + (
                                   sale_order_ref.carrier_acc_no or "N/A") + "<br/>" + \
                           "<strong> Delivery Method #:  </strong>" + (sale_order_ref.carrier_id.name or "N/A")
                           + "<br/>" + "<strong> Date: </strong>" + \
                           (str(datetime.strptime(str(picking.scheduled_date), "%Y-%m-%d %H:%M:%S").strftime(
                               '%m/%d/%Y')) if picking.scheduled_date else "N/A") + \
                           "<br/><strong> Customer Name:  </strong>" + (
                                   sale_order_ref.partner_id.name or "") + "<br/>" + \
                           "<strong> Shipping Address: </strong> <br/>" + shipping_adrs + "<br/>" + \
                           "<strong> Notes :  </strong>" + (picking.note or "N/A"),

            'header': ['Catalog number', 'Description', 'Initial Quantity', 'Lot', 'Expiration Date', 'Quantity Done'],
            'columnProps': ['sku', 'Product', 'qty', 'lot_name', 'lot_expired_date', 'qty_done'],
            'closing_content': 'Thanks & Regards, <br/> Sales Team'
        }

        self.process_common_email_notification_template(super_user, None, vals['subject'], vals['description'],
                                                        vals['sale_order_lines'], vals['header'],
                                                        vals['columnProps'], vals['closing_content'],
                                                        self.warehouse_email, picking)
        '''for user in users:
            has_group = user.has_group('stock.group_stock_manager')
            if has_group:
                self.process_common_email_notification_template(super_user, user, vals['subject'], vals['description'],
                                                                vals['sale_order_lines'], vals['header'],
                                                                vals['columnProps'], vals['closing_content'],
                                                                self.warehouse_email)'''

    def po_receive_notification_for_acquisitions_manager(self, picking):
        Stock_Moves_list = self.env['stock.move'].search([('picking_id', '=', picking.id)])
        Stock_Moves_line = []
        for stock_move in Stock_Moves_list:
            temp = self.env['stock.move.line'].search([('move_id', '=', stock_move.id)])
            Stock_Moves_line.append(temp)
        super_user = self.env['res.users'].search([('id', '=', SUPERUSER_ID_INFO), ])

        sales_order = []
        for stock_move_line_single in Stock_Moves_list:
            lot_name_list = None
            lot_expired_date = None
            qty_done_in_lot = None
            temp = self.env['stock.move.line'].search([('move_id', '=', stock_move.id)])
            for s_move_line in temp:
                if s_move_line.lot_id is not None and s_move_line.lot_id.name: lot_name_list = lot_name_list + '</li> <li style = "list-style-type: none;">' + s_move_line.lot_id.name if lot_name_list is not None else '<ul style="list-style-type: none; padding: 5px;"> <li style = " white-space: nowrap;list-style-type: none;">' + s_move_line.lot_id.name
                if s_move_line.lot_id is not None and s_move_line.lot_id.use_date: lot_expired_date = lot_expired_date + '</li> <li style = "white-space: nowrap; list-style-type: none;">' + s_move_line.lot_id.use_date if lot_expired_date is not None else '<ul style="list-style-type: none; padding: 5px;"><li style = "white-space: nowrap; list-style-type: none;">' + s_move_line.lot_id.use_date
                if s_move_line is not None and s_move_line.qty_done: qty_done_in_lot = qty_done_in_lot + '</li> <li style = "list-style-type: none;">' + str(
                    int(s_move_line.qty_done)) if qty_done_in_lot is not None and s_move_line.qty_done else '<ul style="list-style-type: none; padding: 5px;"><li style = "list-style-type: none;">' + str(
                    int(s_move_line.qty_done))
            lot_name_list = lot_name_list + '</li></ul>' if lot_name_list is not None else ''
            lot_expired_date = lot_expired_date + '</li></ul>' if lot_expired_date is not None else ''
            qty_done_in_lot = qty_done_in_lot + '</li></ul>' if qty_done_in_lot is not None else ''

            sale_order = {
                'sales_order': picking.purchase_id.name,
                'sku': stock_move_line_single.product_id.product_tmpl_id.sku_code,
                'Product': stock_move_line_single.product_id.name,
                'qty': int(stock_move_line_single.ordered_qty),

                'lot_name': lot_name_list,
                'lot_expired_date': lot_expired_date,
                'qty_done_in_lot': qty_done_in_lot,

                'qty_done': int(stock_move_line_single.product_uom_qty),
                'status': "Complete" if int(stock_move_line_single.ordered_qty) == int(
                    stock_move_line_single.product_uom_qty) else "Short" if int(
                    stock_move_line_single.ordered_qty) > int(stock_move_line_single.product_uom_qty) else "Extra"
            }
            sales_order.append(sale_order)
        sale_order_ref = picking.purchase_id
        str_note = ""
        # if sale_order_ref.notes_activity:
        #     for note in sale_order_ref.notes_activity:
        #         str_note = str_note + note.note + " " +  (str(datetime.strptime(note.note_date, "%Y-%m-%d %H:%M:%S").strftime( '%m/%d/%Y')) if note.note_date else "N/A")  + " <br/>    "
        # else:
        #     str_note = "N/A"
        # table_data= " <table style = \"width:100%\">" \
        #      "<tr><td style = \"width:30%\" ><strong>Please proceed Purchase Order</strong></td><td>"+sale_order_ref.name+"</td></tr>" \
        #      "<tr><td><strong> Date </strong> </td><td>" + (str(datetime.strptime(picking.scheduled_date, "%Y-%m-%d %H:%M:%S").strftime( '%m/%d/%Y')) if picking.scheduled_date else "N/A") + "</td></tr>" \
        #      "<tr><td> <strong> Vendor Name </strong></td> <td> "+ ( sale_order_ref.partner_id.name or "") + "</td></tr>"\
        #      "<tr><td> <strong> Notes </strong></td><td>" + str_note + "</td></tr></table>"
        flag = True
        table_data = " <table style = \"width:100%\"> <tr> <td><strong> Notes :</strong></td>"
        if sale_order_ref.notes_activity:
            for note in sale_order_ref.notes_activity:
                if flag == True:
                    flag = False
                    table_data = table_data + "<td style = \"width:30%\"> " + note.note + " </td>" \
                                                                                          " <td> " + (
                                     str(datetime.strptime(str(note.note_date), "%Y-%m-%d %H:%M:%S").strftime(
                                         '%m/%d/%Y')) if note.note_date else "N/A") + " </td> </tr> "
                else:
                    table_data = table_data + "<tr>" \
                                              "<td></td> " \
                                              "<td>" + note.note + "</td> " \
                                                                   "<td> " + (
                                     str(datetime.strptime(str(note.note_date), "%Y-%m-%d %H:%M:%S").strftime(
                                         '%m/%d/%Y')) if note.note_date else "N/A") + "</td> " \
                                                                                      "</tr> "
        table_data = table_data + "</table>"
        vals = {
            'sale_order_lines': sales_order,
            'subject': "Shipment Done For Purchase Order # " + picking.purchase_id.name,
            # 'description': "Hi acquisitions Team, <br/><br/> ",
            # 'description': "Hi Acquisitions Team, <br/><br/> " +
            #                "<div style=\"text-align: center;width: 100%;\"><strong>The Shipment has been completed!</strong></div><br/>" + table_data,
            'description': "Hi Acquisitions Team, <br/><br/> " +
                           "<div style=\"text-align: center;width: 100%;\"><strong>The Shipment has been completed!</strong></div><br/>" +
                           "<strong> Please proceed  Purchase Order : </strong>" + sale_order_ref.name + "<br/>" + \
                           "<strong> Date : </strong>" + (
                               str(datetime.strptime(str(picking.scheduled_date), "%Y-%m-%d %H:%M:%S").strftime(
                                   '%m/%d/%Y')) if picking.scheduled_date else "N/A") + \
                           "<br/><strong> Vendor Name :  </strong>" + (
                                       sale_order_ref.partner_id.name or "") + "<br/>" + table_data,

            'header': ['Catalog number', 'Description', 'Initial Quantity', 'Lot', 'Expiration Date', 'Qty Put In Lot',
                       'Quantity Done', 'Status'],
            'columnProps': ['sku', 'Product', 'qty', 'lot_name', 'lot_expired_date', 'qty_done_in_lot', 'qty_done',
                            'status'],
            'closing_content': 'Thanks & Regards, <br/> Team'
        }

        # Email Attachment
        # template_id = template = self.env.ref("inventory_notification.common_mail_template").with_context(local_context).sudo().send_mail(SUPERUSER_ID_INFO,
        #                                                                             raise_exception=True)
        # # File Attachment Code
        # if not picking is None:
        #     docids = self.env['sale.packing_list_popup'].get_packing_report(picking.purchase_id)
        #     data = None
        #     pdf = \
        #     self.env.ref('packing_list.action_report_inventory_packing_list_pdf').render_qweb_pdf(docids, data=data)[0]
        #     values1 = {}
        #     values1['attachment_ids'] = [(0, 0, {'name': picking.origin,
        #                                          'type': 'binary',
        #                                          'mimetype': 'application/pdf',
        #                                          'datas_fname': 'Packing_List_' + (picking.origin) + '.pdf',
        #                                          'datas': base64.b64encode(pdf)})]
        #
        #     values1['model'] = None
        #     values1['res_id'] = False
        #
        #     self.env['mail.mail'].sudo().browse(template_id).write(values1)

        self.process_common_email_acquisitions_manager_notification_template1(super_user, None, vals['subject'],
                                                                              vals['description'],
                                                                              vals['sale_order_lines'], vals['header'],
                                                                              vals['columnProps'],
                                                                              vals['closing_content'],
                                                                              self.all_email, picking)

    def out_notification_for_sale(self, picking):
        Stock_Moves = self.env['stock.move'].search([('picking_id', '=', picking.id)])
        super_user = self.env['res.users'].search([('id', '=', SUPERUSER_ID_INFO), ])
        users = self.env['res.users'].search([('active', '=', True), ('id', '=', picking.sale_id.user_id.id)])
        sales_order = []
        for stock_move in Stock_Moves:
            sale_order = {
                'sales_order': picking.sale_id.name,
                'sku': stock_move.product_id.product_tmpl_id.sku_code,
                'Product': stock_move.product_id.name,
                'qty': int(stock_move.product_qty)
            }
            sales_order.append(sale_order)
        if picking.carrier_tracking_ref:
            tracking = str(picking.carrier_tracking_ref)
        else:
            tracking = ""
        if picking.sale_id and picking.sale_id.partner_id and picking.sale_id.partner_id.name:
            partner_name = picking.sale_id.partner_id.name
        else:
            partner_name = ""

        _logger.info("#picking_note#")
        _logger.info(picking.note)
        vals = {
            'sale_order_lines': sales_order,
            'subject': "Sale Order # " + picking.sale_id.name + " is Out for Delivery for customer " + partner_name,
            'description': "Hi " + (
                        picking.sale_id.user_id.display_name or "Salesperson") + ",<br><br> Please find detail Of Sale Order: "
                           + picking.sale_id.name + " and their tracking is " + tracking +
                           "<br><br> <strong> Notes : </strong>" + str(picking.note or "N/A") + "",
            'header': ['Catalog number', 'Description', 'Quantity'],
            'columnProps': ['sku', 'Product', 'qty'],
            'closing_content': 'Thanks & Regards, <br/> Warehouse Team'
        }
        print("Inside Out")
        print(users.email)
        self.process_common_email_notification_template(super_user, users, vals['subject'],
                                                        vals['description'], vals['sale_order_lines'], vals['header'],
                                                        vals['columnProps'], vals['closing_content'], None)

    def process_in_stock_scheduler(self, limit):
        _logger.info("process_in_stock_scheduler called - limit %s", str(limit))
        # email_queue = []
        today_date = date.today()
        today_start = today_date
        customers = self.env['res.partner'].search(
            [('customer_rank', '>=', 1), ('is_parent', '=', True), ('email', '!=', ''), ('active', '=', True),
             ('todays_notification', '=', True)], order='id asc', limit=int(limit))

        super_user = self.env['res.users'].search([('id', '=', SUPERUSER_ID_INFO), ])
        start = time.time()
        count = 0
        for customr in customers:
            count = count + 1
            _logger.info("@Processing Count Of Customer = >")
            _logger.info(str(count) + " / " + str(len(customers)))
            # if (customr.email not in email_queue):
            _logger.info(customr.email)
            _logger.info("customr.start_date")
            _logger.info(customr.start_date)
            _logger.info("customr.end_date")
            _logger.info(customr.end_date)
            if (customr.start_date == False and customr.end_date == False) \
                    or (customr.end_date != False and InventoryNotificationScheduler.string_to_date(
                customr.end_date) >= today_start) \
                    or (customr.start_date != False and InventoryNotificationScheduler.string_to_date(
                customr.start_date) <= today_start) \
                    or (
                    customr.start_date != False and customr.end_date != False and InventoryNotificationScheduler.string_to_date(
                customr.start_date) <= today_start and InventoryNotificationScheduler.string_to_date(
                customr.end_date) >= today_start) \
                    or (customr.end_date is None):
                to_customer = customr
                contacts = self.env['res.partner'].search(
                    [('parent_id', '=', customr.id), ('email', '!=', ''), ('active', '=', True)])
                _logger.info("contacts")
                _logger.info(contacts)
                product_list = []
                cust_ids = []
                cust_ids.append(customr.id)
                email_list_cc = []
                for contact in contacts:
                    # if (contact.email not in email_queue):
                    if (contact.email != customr.email and contact.email not in email_list_cc):
                        if (contact.start_date == False and contact.end_date == False) \
                                or (contact.start_date == False and InventoryNotificationScheduler.string_to_date(
                            contact.end_date) and InventoryNotificationScheduler.string_to_date(
                            contact.end_date) >= today_start) \
                                or (contact.end_date == False and InventoryNotificationScheduler.string_to_date(
                            contact.start_date) and InventoryNotificationScheduler.string_to_date(
                            contact.start_date) <= today_start) \
                                or (InventoryNotificationScheduler.string_to_date(
                            contact.start_date) and InventoryNotificationScheduler.string_to_date(
                            contact.start_date) <= today_start and InventoryNotificationScheduler.string_to_date(
                            contact.end_date) and InventoryNotificationScheduler.string_to_date(
                            contact.end_date) >= today_start):
                            cust_ids.extend(contact.ids)
                            _logger.info("cc Customer =")
                            _logger.info(contact.email)
                            if contact.type not in ['other','invoice']:
                                email_list_cc.append(contact.email)
                        # email_queue.append(contact.email)
                if (customr.historic_months > 0):
                    historic_day = customr.historic_months * 30
                    # _logger.info("historic_day :%r", historic_day)
                    last_day = fields.Date.to_string(datetime.now() - timedelta(days=historic_day))
                    # _logger.info("date order  :%r", last_day)
                    sales = self.env['sale.order'].search(
                        [('partner_id', 'in', cust_ids), ('date_order', '>', last_day)])
                else:
                    # historic_day = 36 * 30
                    # _logger.info("historic_day :%r", historic_day)
                    # last_day = fields.Date.to_string(datetime.now() - timedelta(days=historic_day))
                    sales = self.env['sale.order'].search([('partner_id', 'in', cust_ids)])
                # _logger.info("sales  :%r", sales)
                products = {}
                for sale in sales:
                    sale_order_lines = self.env['sale.order.line'].search([('order_id.id', '=', sale.id)])
                    for line in sale_order_lines:
                        # _logger.info(" product_id qty_available %r", line.product_id.actual_quantity)
                        if line.product_id.actual_quantity and line.product_id.actual_quantity is not None and line.product_id.actual_quantity > 0 and line.product_id.product_tmpl_id.sale_ok and line.product_id.active and line.product_id.product_tmpl_id.active and line.product_id.product_tmpl_id.is_published:
                            products[line.product_id.id] = line.product_id
                subject = "SPS Updated In-Stock Product Report"
                descrption = "<strong>Good morning " + customr.name + "</strong>" \
                                                                      "<br/> <br/> Below are items you have previously requested that are currently in stock. " \
                                                                      "In addition, below is the link to download full product catalog. Please let us know what" \
                                                                      " ordering needs we can help provide savings on this week! <br/> <a href='https://www.shopsps.com/downloadCatalog'>Click Here to Download SPS Product Catalog </a>" \
                                                                      """<br/><center>
                                                                      <br/><br/><div style="display: inline-block;position: relative;">
                                                                      <i class="fa fa-1x fa-asterisk" style="color:red;position: absolute;margin-top: -20px;"/>
                                                                      </div>
                                                                      <span style="font-size:24px; margin-left: 24px;">Want to place an order? Click Buy Now! </span>
                                                                      
                                                                      <div style="display: inline-block;position: relative;">
                                                                      <i class="fa fa-1x fa-asterisk" style="color:red;position: absolute;margin-top: -20px;margin-left: 7px"/>
                                                                      </div>
                                                                      <br/> <br/> 
                                                                      <i class="fa fa-1x fa-arrow-down" style="color:red;font-size:24px;"/><br/> <br/>
                                                                                <a target="_blank" href="/shop/quote_my_report/""" + str(
                    customr.id) + """" style="background-color:#1abc9c; padding:15px 60px 15px 60px; text-decoration:none; color:#fff; border-radius:5px; font-size:25px; box-shadow: 0 8px 16px 0 #a29c9c, 0 6px 20px 0 #b2b0b0; " class="o_default_snippet_text">BUY NOW</a>
                                                                        </center><br/><br/>"""
                header = ['Manufacturer', 'Catalog number', 'Description', 'Sales Price', 'Quantity On Hand',
                          'Min Exp. Date',
                          'Max Exp. Date', 'Unit Of Measure']
                columnProps = ['product_brand_id.name', 'sku_code', 'name', 'customer_price_list', 'actual_quantity',
                               'minExDate',
                               'maxExDate', 'uom_id.name']
                closing_content = """
                                    Please reply to this email or contact your Account Manager to hold product or place an order here.
                                    <br/> Many Thanks,
                                    <br/> SPS Customer Care <br/>

                                    <br/>
                                    <table style="height: 96px; width: 601px;" border="0">
                                    <tbody>
                                    <tr style="height: 78px;">
                                    <td style="width: 156px; height: 78px;">
                                    <p style="text-align: left;"><strong>Brittany Edwards</strong></p>
                                    <p style="text-align: left;">412-434-0214</p>
                                    </td>
                                    <td style="width: 154px; height: 78px;">
                                    <p><strong>Chelsea Owen</strong></p>
                                    <p>412-564-1281&nbsp;</p>
                                    </td>
                                    <td style="width: 157px; height: 78px;">
                                    <p style="text-align: left;"><strong>Phil Kemp</strong></p>
                                    <p style="text-align: left;">412-745-1327</p>
                                    </td>
                                    <td style="width: 123px; height: 78px;">&nbsp;</td>
                                    </tr>
                                    <tr style="height: 76px;">
                                    <td style="width: 156px; height: 76px;">
                                    <p><strong>Christopher Odell</strong></p>
                                    <p>412-745-0338</p>
                                    </td>
                                    <td style="width: 157px; height: 76px;">
                                    <p style="text-align: left;"><strong>Rachel Buck&nbsp;</strong></p>
                                    <p style="text-align: left;">412-745-2343&nbsp;&nbsp;</p>
                                    </td>
                                    <td style="width: 123px; height: 76px;">
                                    <p style="text-align: left;"><strong>Kristina Parsons&nbsp;</strong></p>
                                    <p style="text-align: left;">412-248-1284</p>
                                    </td>
                                    </tr>
                                    </tbody>
                                    </table>
                                    <br/>
                                    <div class="text-center" style="text-align: center;">
                                        <a target="_blank" href="/shop/quote_my_report/""" + str(customr.id) + """" style="background-color:#1abc9c; padding:15px 60px 15px 60px; text-decoration:none; color:#fff; border-radius:5px; font-size:25px; box-shadow: 0 8px 16px 0 #a29c9c, 0 6px 20px 0 #b2b0b0;" class="o_default_snippet_text">BUY NOW</a>
                                    </div>

                                    """
                if products:
                    product_list.extend(list(products.values()))
                    # Remove excluded product from list
                    excluded_products = self.env['exclude.product.in.stock'].search([('partner_id', '=', customr.id)])
                    if excluded_products:
                        for excluded_product in excluded_products:
                            if excluded_product.product_id in product_list:
                                product_list.remove(excluded_product.product_id)

                    if customr.user_id.email:
                        email_list_cc.append(customr.user_id.email)
                    if customr.account_manager_cust.email:
                        email_list_cc.append(customr.account_manager_cust.email)
                    sort_col = True
                    self.process_email_in_stock_scheduler_template(super_user, customr, subject, descrption,
                                                                   product_list,
                                                                   header, columnProps, closing_content,
                                                                   customr.email,
                                                                   email_list_cc, sort_col, is_employee=False,
                                                                   partner_id=customr)
            else:
                pass
            customr.todays_notification = False
        end = time.time()
        _logger.info("Time for Execution")
        _logger.info(end - start)

    @api.model
    # @api.multi
    def process_notification_scheduler_everyday(self, custom_date=None):
        self.process_new_product_scheduler()
        self.process_notify_available()
        self.process_packing_list()
        self.process_on_hold_customer()
        if custom_date is not None:
            custom_date = datetime.strptime(custom_date, '%Y-%m-%d').date()
        else:
            custom_date = date.today()
        self.process_todays_notification_flag_scheduler(custom_date)

    def process_todays_notification_flag_scheduler(self, custom_date):
        _logger.info('process_todays_notification_flag_scheduler called')

        today_date = custom_date
        today_start = today_date
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        dayName = today_date.weekday()
        weekday = days[dayName]

        customers = self.env['res.partner'].search(
            [('customer_rank', '>=', 1), ('is_parent', '=', True), ('email', '!=', ''), ('active', '=', True),
             (weekday, '=', True), ('todays_notification', '=', False)])

        for customer in customers:
            try:
                if (customer.start_date == False and customer.end_date == False) \
                        or (customer.end_date != False and InventoryNotificationScheduler.string_to_date(
                    customer.end_date) >= today_start) \
                        or (customer.start_date != False and InventoryNotificationScheduler.string_to_date(
                    customer.start_date) <= today_start) \
                        or (
                        customer.start_date != False and customer.end_date != False and InventoryNotificationScheduler.string_to_date(
                    customer.start_date) <= today_start and InventoryNotificationScheduler.string_to_date(
                    customer.end_date) >= today_start) \
                        or (customer.end_date is None):
                    customer.write({'todays_notification': True})
            except Exception as e:
                _logger.exception(e)

    def process_new_product_scheduler(self):
        today_date = datetime.now() - timedelta(days=1)
        today_start = datetime.strftime(today_date, "%Y-%m-%d 00:00:00")
        products = self.env['product.product'].search(
            [('create_date', '>=', today_start), ('notification_date', '=', None),
             ('product_tmpl_id.type', '=', 'product')])
        subject = "New Product In Inventory"
        descrption = "Hi Team, <br><br/> Please find below a listing of some new products added to the inventory today:"
        header = ['Catalog #', 'Description', 'Sales Price', 'Cost', 'Product Type', 'Min Expiration Date',
                  'Max Expiration Date', 'Quantity On Hand', 'Forecasted Quantity', 'Unit Of Measure']
        columnProps = ['sku_code', 'product_name', 'sale_price', 'standard_price', 'product_type', 'minExpDate',
                       'maxExpDate', 'qty_on_hand', 'forecasted_qty', 'unit_of_measure']
        closing_content = "Thanks & Regards,<br/>Warehouse Team"

        self.process_common_product_scheduler(subject, descrption, products, header, columnProps, closing_content,
                                              self.sales_email)

    def process_packing_list(self):
        today_date = date.today()
        today_start = datetime.now().date()
        final_date = datetime.strftime(today_start, "%Y-%m-%d 00:00:00")
        last_day = fields.Date.to_string(datetime.now() - timedelta(days=2))
        pull_location_id = self.env['stock.location'].search([('name', '=', 'Pull Zone')]).id
        if not pull_location_id or pull_location_id is None:
            pull_location_id = self.env['stock.location'].search([('name', '=', 'Packing Zone')]).id
        picking = self.env['stock.picking'].search(
            [('sale_id.state', '=', 'sale'), ('state', '=', 'done'), ('date_done', '>=', last_day),
             ('location_dest_id', '=', pull_location_id)])
        _logger.info("picking:%r", picking)
        vals = {
            'picking_list': picking,
            'custom_template': "inventory_notification.inventory_packing_list_notification"
        }
        if len(picking) > 0:
            self.process_packing_email_notification(vals)

            # final_date = fields.Datetime.from_string(today_start)
        products = self.env['product.product'].search([('stock_move_ids.sale_line_id', '!=', False),
                                                       ('stock_move_ids.state', '=', 'done'),
                                                       ('stock_move_ids.picking_id', '!=', False),
                                                       ('stock_move_ids.move_line_ids.state', '=', 'done'),
                                                       ('stock_move_ids.move_line_ids.write_date', '>=', last_day),
                                                       ('stock_move_ids.move_line_ids.write_date', '<', final_date),
                                                       ('stock_move_ids.move_line_ids.qty_done', '>', 0),
                                                       ('stock_move_ids.move_line_ids.lot_id', '!=', None)
                                                       ])
        self.process_notification_for_product_red_status(products)

    def process_on_hold_customer(self):
        customers = self.env['res.partner'].search([('on_hold', '=', True), ('is_parent', '=', True)])
        super_user = self.env['res.users'].search([('id', '=', SUPERUSER_ID_INFO), ])
        users = self.env['res.users'].search([('active', '=', True)])
        for customer in customers:
            _logger.info("customer :%r", customer)
        if customers:
            columnProps = ['name', 'user_id.display_name']
            header = ['Serial Number', 'Customer Name', 'Sales Person']
            email_form = super_user
            # email_to = user
            subject = 'Customer On Hold'
            description = 'Hi Shipping Team, <br/><br/>Please find below the list of customers whose "On-hold status" has been released from Accounting Department.'
            closing_content = "Thanks & Regards, <br/> Accounting Team"
            self.process_common_email_notification_template(email_form, None, subject, description,
                                                            customers, header, columnProps, closing_content,
                                                            self.warehouse_email)
            '''for user in users:
                has_group = user.has_group('stock.group_stock_manager') or user.has_group(
                    'sales_team.group_sale_manager')
                if has_group:
                    _logger.info("customer :%r", user)
                    columnProps = ['name', 'user_id.display_name']
                    header = ['Serial Number', 'Customer Name', 'Sales Person']
                    email_form = super_user
                    #email_to = user
                    subject = 'Customer On Hold'
                    description = 'Hi Shipping Team, <br/><br/>Please find below the list of customers whose "On-hold status" has been released from Accounting Department.'
                    closing_content = "Thanks & Regards, <br/> Accounting Team"
                    self.process_common_email_notification_template(email_form, None, subject, description,
                                                                    customers, header, columnProps, closing_content,
                                                                    self.warehouse_email)'''

    def process_hold_off_customer(self, partner_id):
        sales = self.env['sale.order'].search([('state', '=', 'sale'), ('partner_id', '=', partner_id.id)])
        super_user = self.env['res.users'].search([('id', '=', SUPERUSER_ID_INFO), ])
        users = self.env['res.users'].search([('active', '=', True)])
        sales_order = []
        for sale in sales:
            sale_order_lines = self.env['sale.order.line'].search([('order_id.id', '=', sale.id),
                                                                   ('move_ids.state', '=', 'assigned'),
                                                                   ('move_ids.move_line_ids.state', '=', 'assigned')])

            shipping_address = self.check_isAvailable(sale.partner_id.street) + " " + self.check_isAvailable(
                sale.partner_id.street2) + " " \
                               + self.check_isAvailable(sale.partner_id.zip) + " " + self.check_isAvailable(
                sale.partner_id.city) + " " + \
                               self.check_isAvailable(sale.partner_id.state_id.name) + " " + self.check_isAvailable(
                sale.partner_id.country_id.name)
            if sale_order_lines:
                sale_order = {
                    'sales_order': sale.name,
                    'customer_name': sale.partner_id.display_name,
                    'shipping_address': shipping_address
                }
                sales_order.append(sale_order)
        if sales:
            vals = {
                'sale_order_lines': sales_order,
                'subject': "Shipment need to release for " + partner_id.display_name,
                'description': "Hi team, <br/><br/> Payment has been received. Please release the following orders for "
                               "shipping:",
                'header': ['Customer Name', 'Sales order', 'Shipping Address'],
                'columnProps': ['customer_name', 'sales_order', 'shipping_address'],
                'closing_content': "Thanks & Regards, <br/>Accounting Team"
            }
            '''for user in users:
                has_group = user.has_group('stock.group_stock_manager')
                if has_group:'''
            self.process_common_email_notification_template(super_user, None, vals['subject'],
                                                            vals['description'], vals['sale_order_lines'],
                                                            vals['header'],
                                                            vals['columnProps'], vals['closing_content'],
                                                            self.warehouse_email)

    def process_notification_for_product_red_status(self, products):
        super_user = self.env['res.users'].search([('id', '=', SUPERUSER_ID_INFO), ])
        users = self.env['res.users'].search([('active', '=', True)])
        green_products = []
        yellow_products = []
        red_product = []
        switcher = {
            'product': "Stockable",
            'consu': "Consumable",
            'service': "Service"
        }
        for product in products:
            vals = {
                'sku_code': self.check_isAvailable(product.product_tmpl_id.sku_code),
                'sale_price': "$ " + str(product.lst_price) if product.lst_price else "",
                'standard_price': "$ " + str(
                    product.product_tmpl_id.standard_price) if product.product_tmpl_id.standard_price else "",
                'product_type': switcher.get(product.type, " "),
                'qty_on_hand': int(product.actual_quantity),
                'forecasted_qty': int(product.virtual_available),
                'product_name': self.check_isAvailable_product_code(
                    product.default_code) + " " + product.product_tmpl_id.name,
                'unit_of_measure': product.product_tmpl_id.uom_id.name
            }

            if product.inventory_percent_color > 75 and product.inventory_percent_color <= 125:
                yellow_products.append(vals)
            elif product.inventory_percent_color <= 75:
                red_product.append(vals)
        # if yellow_products:
        #     self.process_notify_yellow_product(yellow_products, None, super_user)
        # if red_product:
        #     self.process_notify_red_product(red_product, None, super_user)

        '''for user in users:
            has_group = user.has_group('purchase.group_purchase_manager') or user.has_group(
                'sales_team.group_sale_manager')
            if has_group:
                if yellow_products:
                    self.process_notify_yellow_product(yellow_products, user, super_user)
                if red_product:
                    self.process_notify_red_product(red_product, user, super_user)'''

    def process_notification_for_product_green_status(self, products):
        super_user = self.env['res.users'].search([('id', '=', SUPERUSER_ID_INFO), ])
        users = self.env['res.users'].search([('active', '=', True)])
        green_products = []
        yellow_products = []
        red_product = []
        switcher = {
            'product': "Stockable",
            'consu': "Consumable",
            'service': "Service"
        }
        for product in products:
            vals = {
                'sku_code': self.check_isAvailable(product.product_tmpl_id.sku_code),
                'sale_price': "$ " + str(product.lst_price) if product.lst_price else "",
                'standard_price': "$ " + str(
                    product.product_tmpl_id.standard_price) if product.product_tmpl_id.standard_price else "",
                'product_type': switcher.get(product.type, " "),
                'qty_on_hand': int(product.actual_quantity),
                'forecasted_qty': int(product.virtual_available),
                'product_name': self.check_isAvailable_product_code(
                    product.default_code) + " " + product.product_tmpl_id.name,
                'unit_of_measure': product.product_tmpl_id.uom_id.name
            }
            if product.inventory_percent_color > 125:
                green_products.append(vals)
        # if green_products:
        #     self.process_notify_green_product(green_products, None, super_user)
        # if yellow_products:
        #     self.process_notify_yellow_product(yellow_products, None, super_user)

        '''for user in users:
            has_group = user.has_group('purchase.group_purchase_manager') or user.has_group(
                'sales_team.group_sale_manager')
            if has_group:
                if green_products:
                    self.process_notify_green_product(green_products, user, super_user)
                if yellow_products:
                    self.process_notify_yellow_product(yellow_products, user, super_user)'''

    def process_notification_for_in_stock_report(self, products):
        _logger.info("process_notification_for_in_stock_report called....")
        today_date = date.today()
        today_start = fields.Date.to_string(today_date)
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        dayName = today_date.weekday()
        weekday = days[dayName]
        super_user = self.env['res.users'].search([('id', '=', SUPERUSER_ID_INFO), ])
        _logger.info("weekday: %r", weekday)
        custmer_user = self.env['res.users'].search([('partner_id.customer', '=', True), ('active', '=', True)])
        for customer in custmer_user:
            user = self.env['res.partner'].search(
                [(weekday, '=', True), ('customer', '=', True), ('start_date', '<=', today_start),
                 ('end_date', '>=', today_start), ('id', '=', customer.partner_id.id)])
            if user and products:
                _logger.info("user:%r ", user)
                subject = "In Stock Product"
                description = "Please find below list of all the product whose are in stock in SPS Inventory."
                header = ['Manufacturer', 'Sku Reference', 'Product Code', 'Product Name', 'Qty In Stock',
                          'Product Price', 'Min Expiration Date', 'Max Expiration Date']
                columnProps = ['manufacturer', 'sku_reference', 'product_code', 'product_name', 'actual_quantity',
                               'product_price_symbol', 'minExDate', 'maxExDate']
                closing_content = "Thanks & Regards, <br/> Warehouse Team"
                self.process_common_email_notification_template(super_user, user, subject,
                                                                description, products, header, columnProps,
                                                                closing_content)

    def process_notify_green_product(self, products, to_user, from_user):
        pass
        # subject = "Products which are in green status"
        # description = "Hi Team, <br><br/>Please find a listing below of products whose inventory level status is now Color(Green):"
        # header = ['Catalog #', 'Product Description', 'Sales Price', 'Cost', 'Product Type',
        #           'Quantity On Hand', 'Forecasted Quantity', 'Unit Of Measure']
        # columnProps = ['sku_code', 'product_name', 'sale_price', 'standard_price', 'product_type',
        #                'qty_on_hand', 'forecasted_qty', 'unit_of_measure']
        # closing_content = "Thanks & Regards,<br/> Admin Team"
        # self.process_common_email_notification_template(from_user, to_user, subject,
        #                                                 description, products, header, columnProps, closing_content,
        #                                                 self.acquisitions_email)

    def process_notify_yellow_product(self, products, to_user, from_user):
        pass
        # subject = "Products which are in yellow status"
        # description = "Hi Team, <br><br/>Please find a listing below of products whose inventory level status is now Color(Yellow):"
        # header = ['Catalog #', 'Product Description', 'Sales Price', 'Cost', 'Product Type',
        #           'Qty On Hand', 'Forecasted Quantity', 'Unit Of Measure']
        # columnProps = ['sku_code', 'product_name', 'sale_price', 'standard_price', 'product_type',
        #                'qty_on_hand', 'forecasted_qty', 'unit_of_measure']
        # closing_content = "Thanks & Regards,<br/> Admin Team"
        # self.process_common_email_notification_template(from_user, to_user, subject,
        #                                                 description, products, header, columnProps, closing_content,
        #                                                 self.acquisitions_email)

    def process_notify_red_product(self, products, to_user, from_user):
        pass
        # subject = "Products which are in red status"
        # description = "Hi Team, <br><br/>Please find a listing below of products whose inventory level status is now Color(Red):"
        # header = ['Catalog #', 'Product Description', 'Sales Price', 'Cost', 'Product Type',
        #           'Qty On Hand', 'Forecasted Quantity', 'Unit Of Measure']
        # columnProps = ['sku_code', 'product_name', 'sale_price', 'standard_price', 'product_type',
        #                'qty_on_hand', 'forecasted_qty', 'unit_of_measure']
        # closing_content = "Thanks & Regards,<br/> Admin Team"
        # self.process_common_email_notification_template(from_user, to_user, subject,
        #                                                 description, products, header, columnProps, closing_content,
        #                                                 self.acquisitions_email)

    def process_notify_low_product(self, products, to_user, from_user, max_inventory_level_duration):
        subject = "Products which are in Low Stock"
        description = "Hi Team, <br><br/>Please find a listing below of products whose inventory level status is now Color(Red) : <br/><br/> <b>On Basis of Max Inventory Level Duration </b>  : " + str(
            max_inventory_level_duration) + " Days"
        header = ['Catalog #', 'Product Description', 'Sales Price', 'Cost', 'Product Type',
                  'Qty On Hand', 'Forecasted Quantity', 'Unit Of Measure', 'Current inventory Level',
                  'Max Inventory Level', 'Suggested Order Qty', 'Price Range']
        columnProps = ['sku_code', 'product_name', 'sale_price', 'standard_price', 'product_type',
                       'qty_on_hand', 'forecasted_qty', 'unit_of_measure', 'current_inventory_percent',
                       'max_inventory_level', 'suggested_order_qty', 'price_range']
        closing_content = "Thanks & Regards,<br/> Admin Team"
        _logger.info(" ********low Stock ***** email send **** after prepareing sub,hear etc...... ********")
        self.process_common_email_notification_template(from_user, to_user, subject,
                                                        description, products, header, columnProps, closing_content,
                                                        self.acquisitions_email)

    # this notification send when SO Delivery Out Validate
    def process_notify_low_stock_products(self, products):
        super_user = self.env['res.users'].search([('id', '=', SUPERUSER_ID_INFO), ])

        params = self.env['ir.config_parameter'].sudo()
        max_inventory_level_duration = int(params.get_param('inventory_monitor.max_inventory_level_duration'))

        today_date = datetime.now()
        last_3_months = fields.Date.to_string(today_date - timedelta(days=90))
        cust_location_id = self.env['stock.location'].search([('name', '=', 'Customers')]).id

        red_product = []
        switcher = {
            'product': "Stockable",
            'consu': "Consumable",
            'service': "Service"
        }
        for ml in products:

            if ml.product_tmpl_id.max_inventory_product_level_duration is not None and ml.product_tmpl_id.max_inventory_product_level_duration > 0:
                max_inventory_level_duration = int(ml.product_tmpl_id.max_inventory_product_level_duration)

            quantity = 0
            sale_quant = 0
            purchase_qty = 0
            max_inventory = 0

            max_inventory_percent = 0
            # max_inventory_future_percent = 0
            max_inventory_level = 0
            inventory_percent_color = 0
            # future_percent_color = 0

            product_id = ml
            quant = self.get_quant(cust_location_id, product_id, last_3_months)
            if quant is not None and max_inventory_level_duration > 0:
                sale_quant = sale_quant + int(quant)
                avg_sale_quant = float(sale_quant / 3)
                max_inventory = int((avg_sale_quant) * float(max_inventory_level_duration / 30))
                max_inventory_level = int(max_inventory)
            if product_id.incoming_qty:
                purchase_qty = purchase_qty + int(product_id.incoming_qty)

            quantity = int(product_id.qty_available) + int(quantity)
            qty_in_stock = int(quantity)
            sku_code = ml.product_tmpl_id.sku_code

            if max_inventory > 0:
                # max_inventory_percent = (quantity / int(max_inventory)) * 100
                # inventory_future_percent = ((purchase_qty + qty_in_stock) / int(max_inventory)) * 100

                max_inventory_percent = int((quantity / int(max_inventory)) * 100)
                max_inventory_level = int(max_inventory)
                inventory_percent_color = int(max_inventory_percent)
                # max_inventory_future_percent = int(inventory_future_percent)
                # future_percent_color = int(inventory_future_percent)

            vals = {
                'sku_code': self.check_isAvailable(ml.product_tmpl_id.sku_code),
                'sale_price': "$ " + str(ml.lst_price) if ml.lst_price else "",
                'standard_price': "$ " + str(
                    ml.product_tmpl_id.standard_price) if ml.product_tmpl_id.standard_price else "",
                'product_type': switcher.get(ml.type, " "),
                'qty_on_hand': int(ml.product_tmpl_id.qty_available),
                'forecasted_qty': int(ml.virtual_available),
                'product_name': self.check_isAvailable_product_code(
                    ml.default_code) + " " + ml.product_tmpl_id.name,
                'unit_of_measure': ml.product_tmpl_id.uom_id.name,
                'current_inventory_percent': int(ml.product_tmpl_id.actual_quantity),
                'max_inventory_level': max_inventory_level,
                'suggested_order_qty': round(((max_inventory_level - ml.product_tmpl_id.actual_quantity) / 2)),
                'price_range': '$ ' + str(
                    (float("{0:.2f}".format(ml.product_tmpl_id.list_price * 0.55)))) + ' - $' + str(
                    (float("{0:.2f}".format(ml.product_tmpl_id.list_price * 0.60))))
            }
            if inventory_percent_color <= 75:
                red_product.append(vals)
        if red_product:
            _logger.info(" ********low Stock ***** email send **** after red product fount ******** 1")
            self.process_notify_low_product(red_product, None, super_user, max_inventory_level_duration)
            _logger.info(" ********low Stock ***** email send **** after red product fount ******** 2")

    def process_notify_available(self):
        today_date = date.today()
        today_start = fields.Date.to_string(today_date)
        last_day = fields.Date.to_string(datetime.now() - timedelta(days=1))
        quant = self.env['stock.quant'].search(
            [('create_date', '>=', last_day), ('quantity', '>', 0), ('product_tmpl_id.notify', '=', True), ])
        products = quant.mapped('product_id')
        subject = "Products Back In Stock"
        descrption = "Hi Team, <br><br/> Please find below a listing of products now back in stock:"
        header = ['Catalog #', 'Description', 'Sales Price', 'Cost', 'Product Type', 'Min Expiration Date',
                  'Max Expiration Date',
                  'Quantity On Hand', 'Forecasted Quantity', 'Unit Of Measure']
        columnProps = ['sku_code', 'product_name', 'sale_price', 'standard_price', 'product_type', 'minExpDate',
                       'maxExpDate',
                       'qty_on_hand', 'forecasted_qty', 'unit_of_measure']
        closing_content = "Thanks & Regards,<br/> Warehouse Team"
        self.process_common_product_scheduler(subject, descrption, products, header, columnProps, closing_content,
                                              self.sales_email)
        quant = self.env['stock.quant'].search(
            [('write_date', '>=', last_day), ('quantity', '>', 0), ])
        products = quant.mapped('product_id')
        self.process_notification_for_product_green_status(products)

    def process_packing_email_notification(self, vals):
        super_user = self.env['res.users'].search([('id', '=', SUPERUSER_ID_INFO), ])
        # users = self.env['res.users'].search([('active', '=', True)])
        template = self.env.ref(vals['custom_template'])
        '''for packing in vals['picking_list']:
            print("packing.sale_id.write_date")
            print(packing.sale_id.write_date)'''
        '''for user in users:
            has_group = user.has_group('stock.group_stock_manager')
            if has_group:'''
        local_context = {'picking_list': vals['picking_list'],
                         'subject': 'New Sales Order',
                         'email_from': super_user.email, 'email_to': self.warehouse_email, 'datetime': datetime,
                         'int': int
                         }
        try:
            msg = "\n Email sent --->  " + local_context['subject'] + "\n --From--" + local_context[
                'email_from'] + " \n --To-- " + local_context['email_to']
            _logger.info(msg)
            template.with_context(local_context).sudo().send_mail(SUPERUSER_ID_INFO, raise_exception=True)
        except:
            error_msg = "mail sending fail for email id: %r" + local_context[
                'email_to'] + " sending error report to admin"
            _logger.info(error_msg)
            print(error_msg)

    def process_common_email_notification_template(self, email_from_user, email_to_user, subject, descrption, products,
                                                   header, columnProps, closing_content, email_to_team=None,
                                                   picking=None,
                                                   custom_template="inventory_notification.common_mail_template",
                                                   is_employee=True):
        template = self.env.ref(custom_template)

        product_dict = {}
        product_list = []
        coln_name = []
        serial_number = 0
        background_color = "#f0f8ff"
        for product in products:
            coln_name = []
            query_result = False
            if header[0] == 'Serial Number':
                serial_number = serial_number + 1
                product_dict['Serial Number'] = serial_number
                coln_name.append('Serial Number')
            if background_color == "#ffffff":
                background_color = "#f0f8ff"
            else:
                background_color = "#ffffff"
            if hasattr(product, 'id'):
                stock_warehouse_id = self.env['stock.warehouse'].search([('id', '=', 1), ])
                stock_location_id = self.env['stock.location'].search(
                    [('id', '=', stock_warehouse_id.lot_stock_id.id), ])
                if stock_location_id:
                    self.env.cr.execute(
                        "SELECT  min(use_date), max (use_date) FROM stock_production_lot spl LEFT JOIN   stock_quant sq ON sq.lot_id=spl.id LEFT JOIN  stock_location sl ON sl.id=sq.location_id   where sl.id = %s and  sq.product_id = %s",
                        (stock_location_id.id, product['id'],))
                    query_result = self.env.cr.dictfetchone()
            for column_name in columnProps:
                coln_name.append(column_name)
                if column_name == 'empty':
                    column = ""
                elif column_name == 'minExDate':
                    if query_result and query_result['min']:
                        column = datetime.strptime(str(query_result['min']), "%Y-%m-%d %H:%M:%S")
                    else:
                        column = ""
                elif column_name == 'maxExDate':
                    if query_result and query_result['max']:
                        column = datetime.strptime(str(query_result['max']), "%Y-%m-%d %H:%M:%S")
                    else:
                        column = ""
                else:
                    if isinstance(product, dict):
                        column = str(product.get(column_name))
                    else:
                        if column_name.find(".") == -1:
                            column = str(product[column_name])
                        else:
                            lst = column_name.split('.')
                            column = product[lst[0]]
                            if isinstance(lst, list):
                                for col in range(1, len(lst)):
                                    if column[lst[col]]:
                                        column = column[lst[col]]
                                    else:
                                        column = ""
                            else:
                                column = column[lst]
                if column:
                    product_dict[column_name] = column
                else:
                    product_dict[column_name] = ""
            product_dict['background_color'] = background_color
            product_list.append(product_dict)
            product_dict = {}

        if products:
            vals = {
                'product_list': product_list,
                'headers': header,
                'coln_name': coln_name,
                'email_from_user': email_from_user,
                'email_to_user': email_to_user,
                'email_to_team': email_to_team,
                'subject': subject,
                'description': descrption,
                'template': template,
                'is_employee': is_employee,
                'closing_content': closing_content
            }
            self.send_email_and_notification(vals, picking)

    def send_email_and_notification(self, vals, picking=None):
        email = ""
        if vals['email_to_team']:
            email = vals['email_to_team']
        if vals['email_to_user']:
            email = vals['email_to_user'].sudo().email

        local_context = {'products': vals['product_list'], 'headers': vals['headers'], 'columnProps': vals['coln_name'],
                         'email_from': vals['email_from_user'].sudo().email,
                         'email_to': email, 'subject': vals['subject'],
                         'descrption': vals['description'], 'closing_content': vals['closing_content']}

        html_file = self.env['inventory.notification.html'].search([])
        finalHTML = html_file.process_common_html(vals['subject'], vals['description'], vals['product_list'],
                                                  vals['headers'], vals['coln_name'])

        '''if hasattr(vals['email_to_user'], 'partner_ids'):
            partner_ids = [vals['email_to_user'].partner_ids.id]
        else:
            partner_ids = [vals['email_to_user'].id]'''
        try:
            if email:
                msg = "\n Email sent --->  " + local_context['subject'] + "\n --From--" + local_context[
                    'email_from'] + " \n --To-- " + local_context['email_to']
                _logger.info(msg)

                template_id = vals['template'].with_context(local_context).sudo().send_mail(SUPERUSER_ID_INFO,
                                                                                            raise_exception=True)
                # File Attachment Code
                if not picking is None:
                    # stock_picking_type = self.env['stock.picking.type'].search([('name', '=', 'Delivery Orders')])
                    # stock_out = self.env['stock.picking'].search([('sale_id', '=', picking.sale_id.id), ('picking_type_id', '=', stock_picking_type.id)])

                    docids = self.env['sale.packing_list_popup'].get_packing_report(picking.sale_id)
                    data = None
                    pdf = self.env.ref('packing_list.action_report_inventory_packing_list_pdf').sudo()._render_qweb_pdf(
                        docids,
                        data=data)[
                        0]
                    values1 = {}
                    values1['attachment_ids'] = [(0, 0, {'name': 'Packing_List_' + (picking.origin) + '.pdf',
                                                         'type': 'binary',
                                                         'mimetype': 'application/pdf',
                                                         'store_fname': 'Packing_List' + (picking.origin) + '.pdf',
                                                         'datas': base64.b64encode(pdf)})]

                    values1['model'] = None
                    values1['res_id'] = False

                    self.env['mail.mail'].sudo().browse(template_id).write(values1)
                    # current_mail.mail_message_id.write(values1)
        except:
            error_msg = "mail sending fail for email id: %r" + email + " sending error report to admin"
            _logger.info(error_msg)

    def process_email_in_stock_scheduler_template(self, email_from_user, email_to_user, subject, descrption, products,
                                                  header, columnProps, closing_content, email_to_team, email_list_cc,
                                                  sort_col=False,
                                                  custom_template="inventory_notification.in_stock_scheduler_template",
                                                  is_employee=True, partner_id=None):
        template = self.env.ref(custom_template)
        product_dict = {}
        product_list = []
        coln_name = []
        serial_number = 0
        background_color = "#f0f8ff"
        for product in products:
            coln_name = []
            query_result = False
            if header[0] == 'Serial Number':
                product_dict['Serial Number'] = serial_number + 1
                coln_name.append('Serial Number')
            if background_color == "#ffffff":
                background_color = "#f0f8ff"
            else:
                background_color = "#ffffff"
            if hasattr(product, 'id'):
                stock_warehouse_id = self.env['stock.warehouse'].search([('id', '=', 1), ])
                stock_location_id = self.env['stock.location'].search(
                    [('id', '=', stock_warehouse_id.lot_stock_id.id), ])
                if stock_location_id:
                    self.env.cr.execute(
                        "SELECT  min(use_date), max (use_date) FROM stock_production_lot spl LEFT JOIN   stock_quant sq ON sq.lot_id=spl.id LEFT JOIN  stock_location sl ON sl.id=sq.location_id   where sl.id = %s and  sq.product_id = %s",
                        (stock_location_id.id, product['id'],))
                    query_result = self.env.cr.dictfetchone()
            for column_name in columnProps:
                coln_name.append(column_name)
                if column_name == 'minExDate':
                    if query_result and query_result['min']:
                        min = str(query_result['min'])
                        column = datetime.strptime(str(min), "%Y-%m-%d %H:%M:%S").strftime('%m/%d/%Y')
                    else:
                        column = ""
                elif column_name == 'maxExDate':
                    if query_result and query_result['max']:
                        max = str(query_result['max'])
                        column = datetime.strptime(str(max), "%Y-%m-%d %H:%M:%S").strftime('%m/%d/%Y')
                    else:
                        column = ""
                elif column_name == 'customer_price_list':
                    print("Inside customer_price_list ")
                    column = '$' + " {0:.2f}".format(
                        partner_id.property_product_pricelist.get_product_price(product, product.actual_quantity,
                                                                                partner_id))
                    print(column)
                else:
                    if isinstance(product, dict):
                        column = str(product.get(column_name))
                    else:
                        if column_name.find(".") == -1:
                            if column_name == 'actual_quantity':
                                column = int(product[column_name])
                            elif column_name == 'list_price':
                                column = '$' + " {0:.2f}".format(product[column_name])
                            else:
                                column = str(product[column_name])
                        else:
                            lst = column_name.split('.')
                            column = product[lst[0]]
                            if isinstance(lst, list):
                                for col in range(1, len(lst)):
                                    if column[lst[col]]:
                                        column = column[lst[col]]
                                    else:
                                        column = ""
                            else:
                                column = column[lst]
                if column:
                    product_dict[column_name] = column
                else:
                    product_dict[column_name] = ""
            product_dict['background_color'] = background_color
            product_list.append(product_dict)
            product_dict = {}
        # print(products)
        if products:
            if sort_col:
                product_list = sorted(product_list, key=operator.itemgetter('product_brand_id.name', 'sku_code'))
            vals = {
                'product_list': product_list,
                'headers': header,
                'coln_name': coln_name,
                'email_from_user': email_from_user,
                'email_to_user': email_to_user,
                'email_to_team': email_to_team,
                'subject': subject,
                'description': descrption,
                'template': template,
                'is_employee': is_employee,
                'email_list_cc': email_list_cc,
                'closing_content': closing_content
            }
            self.send_email_in_stock_scheduler_template(vals)

    def send_email_in_stock_scheduler_template(self, vals):
        if vals['email_to_team']:
            email = vals['email_to_team']
        else:
            email = vals['email_to_user'].sudo().email

        local_context = {
            'products': vals['product_list'], 'headers': vals['headers'], 'columnProps': vals['coln_name'],
            'email_from': vals['email_from_user'].sudo().email,
            'email_to': email,
            'subject': vals['subject'],
            'descrption': vals['description'],
            'email_cc': ",".join(vals['email_list_cc']),
            'closing_content': vals['closing_content']
        }
        html_file = self.env['inventory.notification.html'].search([])
        finalHTML = html_file.process_common_html(vals['subject'], vals['description'], vals['product_list'],
                                                  vals['headers'], vals['coln_name'])
        # print(finalHTML)
        if hasattr(vals['email_to_user'], 'partner_ids'):
            partner_ids = [vals['email_to_user'].partner_ids.id]
        else:
            partner_ids = [vals['email_to_user'].id]
        try:
            if vals['email_to_user'].sudo().email:
                msg = "\n Email sent --->  " + local_context['subject'] + "\n --From--" + local_context[
                    'email_from'] + " \n --To-- " + local_context['email_to']
                _logger.info(msg)
                template_id = vals['template'].with_context(local_context).send_mail(SUPERUSER_ID_INFO,
                                                                                     raise_exception=True)
        except:
            erro_msg = "mail sending fail for email id: %r" + vals[
                'email_to_user'].sudo().email + " sending error report to admin"
            _logger.info(erro_msg)
            print(erro_msg)

    def process_common_product_scheduler(self, subject, descrption, products, header, columnProps, closing_content,
                                         email_to_team):
        super_user = self.env['res.users'].search([('id', '=', SUPERUSER_ID_INFO), ])
        users = self.env['res.users'].search([('active', '=', True)])
        today_date = date.today()
        today_start = fields.Date.to_string(today_date)
        switcher = {
            'product': "Stockable",
            'consu': "Consumable",
            'service': "Service"
        }
        if len(products) > 0:
            stock_warehouse_id = self.env['stock.warehouse'].search([('id', '=', 1), ])
            stock_location_id = self.env['stock.location'].search([('id', '=', stock_warehouse_id.lot_stock_id.id), ])
            '''for user in users:
                has_group = user.has_group('sales_team.group_sale_manager')
                if has_group:'''
            product_list = []
            row = "even"
            for product in products:
                query_result = False
                if row == 'even':
                    background_color = "#ffffff"
                    row = "odd"
                else:
                    background_color = "#f0f8ff"
                    row = "even"
                qty_on_hand = product.actual_quantity
                forecasted_qty = product.virtual_available
                if stock_location_id:
                    self.env.cr.execute(
                        "SELECT  min(use_date), max (use_date) FROM stock_production_lot spl LEFT JOIN   stock_quant sq ON sq.lot_id=spl.id LEFT JOIN  stock_location sl ON sl.id=sq.location_id   where sl.id = %s and  sq.product_id = %s",
                        (stock_location_id.id, product.id,))
                    query_result = self.env.cr.dictfetchone()
                if query_result and query_result['min']:
                    minExDate = datetime.strptime(str(query_result['min']), "%Y-%m-%d %H:%M:%S").strftime('%m/%d/%Y')
                else:
                    minExDate = ""
                if query_result and query_result['max']:
                    maxExDate = datetime.strptime(str(query_result['max']), "%Y-%m-%d %H:%M:%S").strftime('%m/%d/%Y')
                else:
                    maxExDate = ""
                vals = {
                    'minExpDate': minExDate,
                    'maxExpDate': maxExDate,
                    'sale_price': "$ " + str(product.lst_price) if product.lst_price else "",
                    'standard_price': "$ " + str(
                        product.product_tmpl_id.standard_price) if product.product_tmpl_id.standard_price else "",
                    'product_type': switcher.get(product.type, " "),
                    'qty_on_hand': int(qty_on_hand or 0),
                    'forecasted_qty': int(forecasted_qty or 0),
                    'background_color': background_color,
                    'product_name': product.product_tmpl_id.name,
                    'sku_code': product.product_tmpl_id.sku_code,
                    'unit_of_measure': product.product_tmpl_id.uom_id.name
                }
                product_list.append(vals)
                product.write({'notification_date': today_start})
            self.process_common_email_notification_template(super_user, None, subject,
                                                            descrption, product_list, header, columnProps,
                                                            closing_content, email_to_team)

    def check_isAvailable(self, value):
        if value:
            return str(value)
        return ""

    def check_isAvailable_product_code(self, value):
        if value:
            return "[" + str(value) + "]"
        return ""

    def process_common_email_acquisitions_manager_notification_template1(self, email_from_user, email_to_user, subject,
                                                                         descrption, products,
                                                                         header, columnProps, closing_content,
                                                                         email_to_team=None,
                                                                         picking=None,
                                                                         custom_template="inventory_notification.mail_template_acquisitions_manager",
                                                                         is_employee=True):
        template = self.env.ref(custom_template)

        product_dict = {}
        product_list = []
        coln_name = []
        serial_number = 0
        background_color = "#f0f8ff"
        for product in products:
            coln_name = []
            query_result = False
            if header[0] == 'Serial Number':
                serial_number = serial_number + 1
                product_dict['Serial Number'] = serial_number
                coln_name.append('Serial Number')
            if background_color == "#ffffff":
                background_color = "#f0f8ff"
            else:
                background_color = "#ffffff"
            if hasattr(product, 'id'):
                stock_warehouse_id = self.env['stock.warehouse'].search([('id', '=', 1), ])
                stock_location_id = self.env['stock.location'].search(
                    [('id', '=', stock_warehouse_id.lot_stock_id.id), ])
                if stock_location_id:
                    self.env.cr.execute(
                        "SELECT  min(use_date), max (use_date) FROM stock_production_lot spl LEFT JOIN   stock_quant sq ON sq.lot_id=spl.id LEFT JOIN  stock_location sl ON sl.id=sq.location_id   where sl.id = %s and  sq.product_id = %s",
                        (stock_location_id.id, product['id'],))
                    query_result = self.env.cr.dictfetchone()
            for column_name in columnProps:
                coln_name.append(column_name)
                if column_name == 'empty':
                    column = ""
                elif column_name == 'minExDate':
                    if query_result and query_result['min']:
                        column = datetime.strptime(str(query_result['min']), "%Y-%m-%d %H:%M:%S")
                    else:
                        column = ""
                elif column_name == 'maxExDate':
                    if query_result and query_result['max']:
                        column = datetime.strptime(str(query_result['max']), "%Y-%m-%d %H:%M:%S")
                    else:
                        column = ""
                else:
                    if isinstance(product, dict):
                        column = str(product.get(column_name))
                    else:
                        if column_name.find(".") == -1:
                            column = str(product[column_name])
                        else:
                            lst = column_name.split('.')
                            column = product[lst[0]]
                            if isinstance(lst, list):
                                for col in range(1, len(lst)):
                                    if column[lst[col]]:
                                        column = column[lst[col]]
                                    else:
                                        column = ""
                            else:
                                column = column[lst]
                if column:
                    product_dict[column_name] = column
                else:
                    product_dict[column_name] = ""
            product_dict['background_color'] = background_color
            product_list.append(product_dict)
            product_dict = {}

        if products:
            vals = {
                'product_list': product_list,
                'headers': header,
                'coln_name': coln_name,
                'email_from_user': email_from_user,
                'email_to_user': email_to_user,
                'email_to_team': email_to_team,
                'subject': subject,
                'description': descrption,
                'template': template,
                'is_employee': is_employee,
                'closing_content': closing_content
            }
            self.send_email_acquisitions_manager_notification(vals, picking)

    def send_email_acquisitions_manager_notification(self, vals, picking=None):
        email = ""
        if vals['email_to_team']:
            email = vals['email_to_team']
        if vals['email_to_user']:
            email = vals['email_to_user'].sudo().email

        local_context = {'products': vals['product_list'], 'headers': vals['headers'], 'columnProps': vals['coln_name'],
                         'email_from': vals['email_from_user'].sudo().email,
                         'email_to': email, 'subject': vals['subject'],
                         'descrption': vals['description'], 'closing_content': vals['closing_content']}

        html_file = self.env['inventory.notification.html'].search([])
        finalHTML = html_file.process_common_html(vals['subject'], vals['description'], vals['product_list'],
                                                  vals['headers'], vals['coln_name'])

        '''if hasattr(vals['email_to_user'], 'partner_ids'):
            partner_ids = [vals['email_to_user'].partner_ids.id]
        else:
            partner_ids = [vals['email_to_user'].id]'''
        try:
            if email:
                msg = "\n Email sent --->  " + local_context['subject'] + "\n --From--" + local_context[
                    'email_from'] + " \n --To-- " + local_context['email_to']
                _logger.info(msg)

                template_id = vals['template'].with_context(local_context).sudo().send_mail(SUPERUSER_ID_INFO,
                                                                                            raise_exception=True)
                # File Attachment Code
                if not picking is None:
                    docids = self.env['stock.move.line'].search([('picking_id', '=', picking.id), ]).ids
                    data = None
                    pdf = \
                        self.env.ref('sps_receiving_list_report.action_sps_receiving_list_report')._render_qweb_pdf(
                            docids,
                            data=data)[
                            0]
                    values1 = {}
                    values1['attachment_ids'] = [(0, 0, {'name': 'Receiving_List_' + (picking.origin) + '.pdf',
                                                         'type': 'binary',
                                                         'mimetype': 'application/pdf',
                                                         'store_fname': 'Receiving_List_' + (picking.origin) + '.pdf',
                                                         'datas': base64.b64encode(pdf)})]

                    values1['model'] = None
                    values1['res_id'] = False

                    self.env['mail.mail'].sudo().browse(template_id).write(values1)
                    # current_mail.mail_message_id.write(values1)
        except:
            error_msg = "mail sending fail for email id: %r" + email + " sending error report to admin"
            _logger.info(error_msg)

    def send_email_after_vendor_offer_conformation(self, purchase_order_id):
        print('send_email_after_vendor_offer_conformation')
        template = self.env.ref("inventory_notification.mail_template_vendor_offer_acceptance")
        super_user_email = self.env['res.users'].search([('id', '=', SUPERUSER_ID_INFO), ]).sudo().email
        purchase_order = self.env['purchase.order'].search([('id', '=', purchase_order_id), ]).ensure_one()
        local_context = {'email_from': super_user_email,
                         'email_to': self.warehouse_email + ', ' + self.sales_email + ', ' + self.appraisal_email,
                         'subject': 'Vendor Offer Acceptance Notification ' + purchase_order.name,
                         'descrption': 'Hi Team, <br><br/> ' + ' Vendor Offer has been accepted for <b>"' + purchase_order.name + '"</b> and Appraisal No# is <b>"' + purchase_order.appraisal_no + '"</b>' + (
                             ' with Offer Type <b>"' + purchase_order.offer_type + '"</b>.' if purchase_order.offer_type else "."),
                         'closing_content': "Thanks & Regards,<br/> Admin Team"}
        try:
            ship_label = None;
            if purchase_order.shipping_number:
                ship_label = self.env['ir.attachment'].search(
                    [('res_model', '=', 'purchase.order'),
                     ('mimetype', '=', 'application/pdf'), ('name', 'ilike', '%'+purchase_order.name+'%'),
                     ('name', 'like', '%FedEx_Label%')], order="id desc")[0]

            data = None
            pdf = self.env.ref('vendor_offer.action_report_vendor_offer_accepted')._render_qweb_pdf(purchase_order_id,
                                                                                                   data=data)[
                0]
            values1 = {}
            values1['attachment_ids'] = [(0, 0, {'name': 'Vendor_Offer_' + (purchase_order.name) + '.pdf',
                                                 'type': 'binary',
                                                 'mimetype': 'application/pdf',
                                                 'store_fname': 'Vendor_Offer_' + purchase_order.name + '.pdf',
                                                 'datas': base64.b64encode(pdf)})
                                         ]

            local_context['descrption'] = local_context[
                                              'descrption'] + ' <br><br/> PFA files for Vendor Offer ' + ' <b>" Vendor_Offer_' + purchase_order.name + '.pdf " </b>'
            if ship_label is not None:
                values1['attachment_ids'].append(
                    (0, 0, {'name': ship_label.name,
                            'type': 'binary',
                            'mimetype': 'application/pdf',
                            'store_fname': ship_label.name,
                            'datas': ship_label.datas})
                )
                local_context['descrption'] = local_context[
                                                  'descrption'] + 'and Shipping label <b> "' + ship_label.name + ' "</b>'

            values1['model'] = None
            values1['res_id'] = False
            template_id = template.with_context(local_context).sudo().send_mail(SUPERUSER_ID_INFO, raise_exception=True)
            self.env['mail.mail'].sudo().browse(template_id).write(values1)

        except:
            error_msg = "mail sending fail for email id: %r" + super_user_email + " sending error report to admin"
            _logger.info(error_msg)

    @staticmethod
    def string_to_date(date_string):
        if date_string == False:
            return None
        datestring = str(date_string)
        return datetime.strptime(str(datestring), DEFAULT_SERVER_DATE_FORMAT).date()

    def get_quant(self, cust_location_id, product_id, last_3_months):
        self.env.cr.execute(
            "SELECT sum(sml.qty_done) FROM sale_order_line AS sol LEFT JOIN stock_picking AS sp ON sp.sale_id=sol.id LEFT JOIN stock_move_line AS sml ON sml.picking_id=sp.id WHERE sml.state='done' AND sml.location_dest_id =%s AND sml.product_id =%s AND sp.date_done>=%s",
            (cust_location_id, product_id.id, last_3_months))
        quant = self.env.cr.fetchone()
        return quant[0]
