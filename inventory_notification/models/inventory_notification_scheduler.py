# -*- coding: utf-8 -*-

from odoo import models, fields, api, SUPERUSER_ID
import logging
from datetime import datetime
from datetime import date, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import time
import operator
_logger = logging.getLogger(__name__)


class InventoryNotificationScheduler(models.TransientModel):
    _name = 'inventory.notification.scheduler'

    #warehouse_email = "vasimkhan@benchmarkitsolutions.com"
    #sales_email = "rohitkabadi@benchmarkitsolutions.com"
    #acquisitions_email = "ajinkyanimbalkar@benchmarkitsolutions.com"

    warehouse_email = "warehouse@surgicalproductsolutions.com"
    sales_email = "salesteam@surgicalproductsolutions.com"
    acquisitions_email = "acquisitions@surgicalproductsolutions.com"

    def process_manual_notification_scheduler(self):
        _logger.info("process_manual_notification_scheduler called..")
        self.process_notification_scheduler()

    @api.model
    @api.multi
    def process_notification_scheduler(self):
        _logger.info("process_notification_scheduler called")
        self.process_in_stock_scheduler()
        self.process_new_product_scheduler()
        self.process_notify_available()
        self.process_packing_list()
        self.process_on_hold_customer()

    def pick_notification_for_customer(self, picking):
        Stock_Moves = self.env['stock.move'].search([('picking_id', '=', picking.id)])
        super_user = self.env['res.users'].search([('id', '=', SUPERUSER_ID), ])
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
        super_user = self.env['res.users'].search([('id', '=', SUPERUSER_ID), ])
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
        vals = {
            'sale_order_lines': sales_order,
            'subject': "Pull Done For Sale Order # " + picking.sale_id.name,
            'header': ['Catalog number', 'Description', 'Quantity'],
            'columnProps': ['sku', 'Product', 'qty'],
            'closing_content': 'Thanks & Regards,<br/> Warehouse Team'
        }
        vals['description'] = "Hi " + picking.sale_id.user_id.display_name + \
                              ", <br/><br/> Please find detail Of Sale Order: " + picking.sale_id.name
        print("Inside Pull")
        print(users.sudo().email)
        self.process_common_email_notification_template(super_user, users, vals['subject'], vals['description'],
                                                        vals['sale_order_lines'], vals['header'],
                                                        vals['columnProps'], vals['closing_content'])
        '''for user in users:
            has_group = user.has_group('stock.group_stock_manager')
            if has_group:
                vals['description'] = "Hi " + user.display_name + \
                                      ", <br/><br/> Please find detail Of Sale Order: " + picking.sale_id.name
                self.process_common_email_notification_template(super_user, user, vals['subject'], vals['description'],
                                                                vals['sale_order_lines'], vals['header'],
                                                                vals['columnProps'], vals['closing_content'])'''

    def pick_notification_for_user(self, picking):
        Stock_Moves_list = self.env['stock.move'].search([('picking_id', '=', picking.id)])
        Stock_Moves_line = []
        for stock_move in Stock_Moves_list:
            temp = self.env['stock.move.line'].search([('move_id', '=', stock_move.id)])
            Stock_Moves_line.append(temp)
        super_user = self.env['res.users'].search([('id', '=', SUPERUSER_ID), ])
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
                }
                sales_order.append(sale_order)
        sale_order_ref = picking.sale_id
        address_ref = sale_order_ref.partner_shipping_id
        vals = {
            'sale_order_lines': sales_order,
            'subject': "Pick Done For Sale Order # " + picking.sale_id.name,
            'description': "Hi Shipping Team, <br/><br/> " +
                           "<div style=\"text-align: center;width: 100%;\"><strong>The PICK has been completed!</strong></div><br/>" +
                           "<strong> Please proceed with the pulling and shipping of Sales Order: </strong>" + sale_order_ref.name + "<br/>" + \
                           "<strong> Customer PO #:  </strong>" + (sale_order_ref.client_order_ref or "N/A") + "<br/>" + \
                           "<strong> Carrier Info:  </strong>" + (sale_order_ref.carrier_info or "N/A") + "<br/>" + \
                           "<strong> Carrier Account #:  </strong>" + (
                                   sale_order_ref.carrier_acc_no or "N/A") + "<br/>" + \
                           "<strong> Delivery Method #:  </strong>" + (sale_order_ref.carrier_id.name or "N/A")
                           + "<br/>" + "<strong> Date: </strong>" + \
                           (str(datetime.strptime(picking.scheduled_date, "%Y-%m-%d %H:%M:%S").strftime(
                               '%m/%d/%Y')) if picking.scheduled_date else "N/A") + \
                           "<br/><strong> Customer Name:  </strong>" + (
                                   sale_order_ref.partner_id.name or "") + "<br/>" + \
                           "<strong> Shipping Address: </strong> " + (address_ref.street or "") + \
                           (address_ref.city or "") + (address_ref.state_id.name or "") + (address_ref.zip or "") + \
                           (address_ref.country_id.name or ""),
            'header': ['Catalog number', 'Description', 'Initial Quantity', 'Lot', 'Expiration Date', 'Quantity Done'],
            'columnProps': ['sku', 'Product', 'qty', 'lot_name', 'lot_expired_date', 'qty_done'],
            'closing_content': 'Thanks & Regards, <br/> Sales Team'
        }
        self.process_common_email_notification_template(super_user, None, vals['subject'], vals['description'],
                                                        vals['sale_order_lines'], vals['header'],
                                                        vals['columnProps'], vals['closing_content'],
                                                        self.warehouse_email)
        '''for user in users:
            has_group = user.has_group('stock.group_stock_manager')
            if has_group:
                self.process_common_email_notification_template(super_user, user, vals['subject'], vals['description'],
                                                                vals['sale_order_lines'], vals['header'],
                                                                vals['columnProps'], vals['closing_content'],
                                                                self.warehouse_email)'''

    def out_notification_for_sale(self, picking):
        Stock_Moves = self.env['stock.move'].search([('picking_id', '=', picking.id)])
        super_user = self.env['res.users'].search([('id', '=', SUPERUSER_ID), ])
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
        vals = {
            'sale_order_lines': sales_order,
            'subject': "Sale Order # " + picking.sale_id.name + " is Out for Delivery for customer " + partner_name,
            'description': "Hi " + picking.sale_id.user_id.display_name + ",<br> Please find detail Of Sale Order: " + picking.sale_id.name + " and their tracking is " + tracking,
            'header': ['Catalog number', 'Description', 'Quantity'],
            'columnProps': ['sku', 'Product', 'qty'],
            'closing_content': 'Thanks & Regards, <br/> Warehouse Team'
        }
        print("Inside Out")
        print(users.email)
        self.process_common_email_notification_template(super_user, users, vals['subject'],
                                                        vals['description'], vals['sale_order_lines'], vals['header'],
                                                        vals['columnProps'], vals['closing_content'], None)

    def process_in_stock_scheduler(self):
        _logger.info("process_in_stock_scheduler called")
        email_queue = []
        today_date = date.today()
        today_start = today_date
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        dayName = today_date.weekday()
        weekday = days[dayName]
        customers = self.env['res.partner'].search(
            [('customer', '=', True), ('is_parent', '=', True), ('email', '!=', ''), ('active', '=', True),
             (weekday, '=', True)])
        super_user = self.env['res.users'].search([('id', '=', SUPERUSER_ID), ])
        start = time.time()
        for customr in customers:
            if (customr.email not in email_queue):
                if (customr.start_date == False and customr.end_date == False) \
                        or (customr.start_date == False and InventoryNotificationScheduler.string_to_date(
                    customr.end_date) >= today_start) \
                        or (customr.end_date == False and InventoryNotificationScheduler.string_to_date(
                    customr.start_date) <= today_start) \
                        or (InventoryNotificationScheduler.string_to_date(
                    customr.start_date) <= today_start and InventoryNotificationScheduler.string_to_date(
                    customr.end_date) >= today_start):
                    print("To Customer =")
                    print(customr.email)
                    email_queue.append(customr.email)
                    _logger.info("customer :%r", customr)
                    to_customer = customr
                    contacts = self.env['res.partner'].search(
                        [('parent_id', '=', customr.id), ('email', '!=', ''), ('active', '=', True)])
                    print("contacts")
                    print(contacts)
                    product_list = []
                    cust_ids = []
                    cust_ids.append(customr.id)
                    email_list_cc = []
                    for contact in contacts:
                        if (contact.email not in email_queue):
                            if (contact.start_date == False and contact.end_date == False) \
                                    or (contact.start_date == False and InventoryNotificationScheduler.string_to_date(
                                contact.end_date) >= today_start) \
                                    or (contact.end_date == False and InventoryNotificationScheduler.string_to_date(
                                contact.start_date) <= today_start) \
                                    or (InventoryNotificationScheduler.string_to_date(
                                contact.start_date) <= today_start and InventoryNotificationScheduler.string_to_date(
                                contact.end_date) >= today_start):
                                cust_ids.extend(contact.ids)
                                print("cc Customer =")
                                print(contact.email)
                                email_list_cc.append(contact.email)
                                email_queue.append(contact.email)
                    if (customr.historic_months > 0):
                        historic_day = customr.historic_months * 30
                        _logger.info("historic_day :%r", historic_day)
                        last_day = fields.Date.to_string(datetime.now() - timedelta(days=historic_day))
                        _logger.info("date order  :%r", last_day)
                        sales = self.env['sale.order'].search(
                            [('partner_id', 'in', cust_ids), ('date_order', '>', last_day)])
                    else:
                        #historic_day = 36 * 30
                        #_logger.info("historic_day :%r", historic_day)
                        #last_day = fields.Date.to_string(datetime.now() - timedelta(days=historic_day))
                        sales = self.env['sale.order'].search([('partner_id', 'in', cust_ids)])
                    _logger.info("sales  :%r", sales)
                    products = {}
                    for sale in sales:
                        sale_order_lines = self.env['sale.order.line'].search([('order_id.id', '=', sale.id)])
                        for line in sale_order_lines:
                            _logger.info(" product_id qty_available %r", line.product_id.actual_quantity)
                            if line.product_id.actual_quantity and line.product_id.actual_quantity is not None and line.product_id.actual_quantity > 0:
                                products[line.product_id.id] = line.product_id
                    subject = "SPS Updated In-Stock Product Report"
                    descrption = "<strong>Good morning " + customr.name + "</strong>" \
                                                                          "<br/> <br/> Below are items you have previously requested that are currently in stock. " \
                                                                          "In addition, below is the link to download full product catalog. Please let us know what" \
                                                                          " ordering needs we can help provide savings on this week! <br/> <a href='/downloadCatalog'>Click Here to Download SPS Product Catalog </a>"
                    header = ['Manufacturer','Catalog number', 'Description', 'Sales Price', 'Quantity On Hand',
                              'Min Exp. Date',
                              'Max Exp. Date', 'Unit Of Measure']
                    columnProps = ['product_brand_id.name','sku_code', 'name', 'list_price', 'actual_quantity', 'minExDate',
                                   'maxExDate', 'uom_id.name']
                    closing_content = "Please reply to this email or contact your Acount Manager to hold product or place an order. " \
                                      "<br/>Many Thanks,		" \
                                      "<br/>SPS Customer Care" \
                                      "<br/>" \
                                      "<br/><strong>Nick Zanetta</strong>" \
                                      "<br/>412-745-0329	" \
                                      "<br/>" \
                                      "<br/><strong>Matt Cochran</strong>" \
                                      "<br/>412-564-9011	" \
                                      "<br/>" \
                                      "<br/><strong>Joe Lamb</strong>	" \
                                      "<br/>412-745-1327	" \
                                      "<br/>" \
                                      "<br/><strong>Brittany Edwards</strong>	" \
                                      "<br/>412-434-0214	" \
                                      "<br/>" \
                                      "<br/><strong>Gabriella Thomas</strong>	" \
                                      "<br/>412-745-0324" \
                                      "<br/>" \
                                      "<br/><strong>Kacie Colteryahn</strong>" \
                                      "<br/>412-745-1325	" \
                                      "<br/>" \
                                      "<br/><strong>Summer Weinberg</strong>" \
                                      "<br/>412-745-0328			"
                    if products:
                        product_list.extend(list(products.values()))
                        if customr.user_id.email:
                            email_list_cc.append(customr.user_id.email)
                        sort_col=True
                        self.process_email_in_stock_scheduler_template(super_user, customr, subject, descrption,
                                                                       product_list,
                                                                       header, columnProps, closing_content,
                                                                       customr.email,
                                                                       email_list_cc,sort_col,is_employee=False)
                else:
                    pass
        end = time.time()
        print("Time for Execution")
        print(end - start)

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
        super_user = self.env['res.users'].search([('id', '=', SUPERUSER_ID), ])
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
        super_user = self.env['res.users'].search([('id', '=', SUPERUSER_ID), ])
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
        super_user = self.env['res.users'].search([('id', '=', SUPERUSER_ID), ])
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
                'sale_price':"$ " + str(product.lst_price) if product.lst_price else "",
                'standard_price': "$ " + str(product.product_tmpl_id.standard_price) if product.product_tmpl_id.standard_price else "",
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
        if yellow_products:
            self.process_notify_yellow_product(yellow_products, None, super_user)
        if red_product:
            self.process_notify_red_product(red_product, None, super_user)

        '''for user in users:
            has_group = user.has_group('purchase.group_purchase_manager') or user.has_group(
                'sales_team.group_sale_manager')
            if has_group:
                if yellow_products:
                    self.process_notify_yellow_product(yellow_products, user, super_user)
                if red_product:
                    self.process_notify_red_product(red_product, user, super_user)'''

    def process_notification_for_product_green_status(self, products):
        super_user = self.env['res.users'].search([('id', '=', SUPERUSER_ID), ])
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
                'standard_price': "$ " + str(product.product_tmpl_id.standard_price) if product.product_tmpl_id.standard_price else "",
                'product_type': switcher.get(product.type, " "),
                'qty_on_hand': int(product.actual_quantity),
                'forecasted_qty': int(product.virtual_available),
                'product_name': self.check_isAvailable_product_code(
                    product.default_code) + " " + product.product_tmpl_id.name,
                'unit_of_measure': product.product_tmpl_id.uom_id.name
            }
            if product.inventory_percent_color > 125:
                green_products.append(vals)
        if green_products:
            self.process_notify_green_product(green_products, None, super_user)
        if yellow_products:
            self.process_notify_yellow_product(yellow_products, None, super_user)

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
        super_user = self.env['res.users'].search([('id', '=', SUPERUSER_ID), ])
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
        subject = "Products which are in green status"
        description = "Hi Team, <br><br/>Please find a listing below of products whose inventory level status is now Color(Green):"
        header = ['Catalog #', 'Product Description', 'Sales Price', 'Cost', 'Product Type',
                  'Quantity On Hand', 'Forecasted Quantity', 'Unit Of Measure']
        columnProps = ['sku_code', 'product_name', 'sale_price', 'standard_price', 'product_type',
                       'qty_on_hand', 'forecasted_qty', 'unit_of_measure']
        closing_content = "Thanks & Regards,<br/> Admin Team"
        self.process_common_email_notification_template(from_user, to_user, subject,
                                                        description, products, header, columnProps, closing_content,
                                                        self.acquisitions_email)

    def process_notify_yellow_product(self, products, to_user, from_user):
        subject = "Products which are in yellow status"
        description = "Hi Team, <br><br/>Please find a listing below of products whose inventory level status is now Color(Yellow):"
        header = ['Catalog #', 'Product Description', 'Sales Price', 'Cost', 'Product Type',
                  'Qty On Hand', 'Forecasted Quantity', 'Unit Of Measure']
        columnProps = ['sku_code', 'product_name', 'sale_price', 'standard_price', 'product_type',
                       'qty_on_hand', 'forecasted_qty', 'unit_of_measure']
        closing_content = "Thanks & Regards,<br/> Admin Team"
        self.process_common_email_notification_template(from_user, to_user, subject,
                                                        description, products, header, columnProps, closing_content,
                                                        self.acquisitions_email)

    def process_notify_red_product(self, products, to_user, from_user):
        subject = "Products which are in red status"
        description = "Hi Team, <br><br/>Please find a listing below of products whose inventory level status is now Color(Red):"
        header = ['Catalog #', 'Product Description', 'Sales Price', 'Cost', 'Product Type',
                  'Qty On Hand', 'Forecasted Quantity', 'Unit Of Measure']
        columnProps = ['sku_code', 'product_name', 'sale_price', 'standard_price', 'product_type',
                       'qty_on_hand', 'forecasted_qty', 'unit_of_measure']
        closing_content = "Thanks & Regards,<br/> Admin Team"
        self.process_common_email_notification_template(from_user, to_user, subject,
                                                        description, products, header, columnProps, closing_content,
                                                        self.acquisitions_email)

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
        super_user = self.env['res.users'].search([('id', '=', SUPERUSER_ID), ])
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
                         'int':int
                         }
        try:
            msg = "\n Email sent --->  " + local_context['subject'] + "\n --From--" + local_context[
                'email_from'] + " \n --To-- " + local_context['email_to']
            _logger.info(msg)
            template.with_context(local_context).sudo().send_mail(SUPERUSER_ID, raise_exception=True)
        except:
            error_msg = "mail sending fail for email id: %r" + local_context[
                'email_to'] + " sending error report to admin"
            _logger.info(error_msg)
            print(error_msg)

    def process_common_email_notification_template(self, email_from_user, email_to_user, subject, descrption, products,
                                                   header, columnProps, closing_content, email_to_team=None,
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
                        column = datetime.strptime(query_result['min'], "%Y-%m-%d %H:%M:%S")
                    else:
                        column = ""
                elif column_name == 'maxExDate':
                    if query_result and query_result['max']:
                        column = datetime.strptime(query_result['max'], "%Y-%m-%d %H:%M:%S")
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
        print("email_to_team")
        print(email_to_team)
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
            self.send_email_and_notification(vals)

    def send_email_and_notification(self, vals):
        print(vals)
        email = ""
        if vals['email_to_team']:
            print("inside 1 st")
            email = vals['email_to_team']
            print(email)
        if vals['email_to_user']:
            print("inside 2 nd")
            email = vals['email_to_user'].sudo().email
            print(email)

        print("email=")
        print(email)

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
                template_id = vals['template'].with_context(local_context).sudo().send_mail(SUPERUSER_ID,
                                                                                            raise_exception=True)
        except:
            error_msg = "mail sending fail for email id: %r" + vals[
                'email_to_user'].sudo().email + " sending error report to admin"
            _logger.info(error_msg)
            print(error_msg)

        # if vals['is_employee']:
        # mail = self.env["mail.thread"]
        # mail.sudo().message_post(
        #     body=finalHTML,
        #     subject=vals['subject'],
        #     message_type='notification',
        #     partner_ids=partner_ids,
        #     content_subtype='html'
        # )

    def process_email_in_stock_scheduler_template(self, email_from_user, email_to_user, subject, descrption, products,
                                                  header, columnProps, closing_content, email_to_team, email_list_cc,sort_col=False,
                                                  custom_template="inventory_notification.in_stock_scheduler_template",
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
                        column = datetime.strptime(query_result['min'], "%Y-%m-%d %H:%M:%S").strftime('%m/%d/%Y')
                    else:
                        column = ""
                elif column_name == 'maxExDate':
                    if query_result and query_result['max']:
                        column = datetime.strptime(query_result['max'], "%Y-%m-%d %H:%M:%S").strftime('%m/%d/%Y')
                    else:
                        column = ""
                else:
                    if isinstance(product, dict):
                        column = str(product.get(column_name))
                    else:
                        if column_name.find(".") == -1:
                            if column_name == 'actual_quantity':
                                column = int(product[column_name])
                            elif column_name == 'list_price':
                                column = '$' + str(product[column_name])
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
                product_list = sorted(product_list,key=operator.itemgetter('product_brand_id.name','sku_code'))
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
                template_id = vals['template'].with_context(local_context).send_mail(SUPERUSER_ID, raise_exception=True)
        except:
            erro_msg = "mail sending fail for email id: %r" + vals[
                'email_to_user'].sudo().email + " sending error report to admin"
            _logger.info(erro_msg)
            print(erro_msg)
            '''try:
                msg = "\n Email sent --->  " + local_context['subject'] + "\n --From--" + local_context[
                    'email_from'] + " \n --To-- " + local_context['email_to']
                _logger.info(msg)
                vals['template'].with_context(local_context).send_mail(SUPERUSER_ID, raise_exception=True)
            except:
                erro_msg = "mail sending fail for email id: %r", vals['email_to_user'].email
                _logger.info(erro_msg)
                print(erro_msg)'''

        # if vals['is_employee']:
        #     mail = self.env["mail.thread"]
        #     mail.message_post(
        #         body=finalHTML,
        #         subject=vals['subject'],
        #         message_type='notification',
        #         partner_ids=partner_ids,
        #         content_subtype='html'
        #     )

    def process_common_product_scheduler(self, subject, descrption, products, header, columnProps, closing_content,
                                         email_to_team):
        super_user = self.env['res.users'].search([('id', '=', SUPERUSER_ID), ])
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
                    minExDate = datetime.strptime(query_result['min'], "%Y-%m-%d %H:%M:%S").strftime('%m/%d/%Y')
                else:
                    minExDate = ""
                if query_result and query_result['max']:
                    maxExDate = datetime.strptime(query_result['max'], "%Y-%m-%d %H:%M:%S").strftime('%m/%d/%Y')
                else:
                    maxExDate = ""
                vals = {
                    'minExpDate': minExDate,
                    'maxExpDate': maxExDate,
                    'sale_price': "$ " + str(product.lst_price) if product.lst_price else "",
                    'standard_price': "$ " + str(product.product_tmpl_id.standard_price) if product.product_tmpl_id.standard_price else "",
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

    @staticmethod
    def string_to_date(date_string):
        # if date_string == False:
        #     return None
        return datetime.strptime(date_string, DEFAULT_SERVER_DATE_FORMAT).date()
