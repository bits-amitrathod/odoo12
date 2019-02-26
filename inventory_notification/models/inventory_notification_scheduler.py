# -*- coding: utf-8 -*-

from odoo import models, fields, api,SUPERUSER_ID
import logging
import datetime
from datetime import date,datetime,timedelta
import base64
import calendar
from odoo.exceptions import UserError
from odoo.tools import float_compare

_logger = logging.getLogger(__name__)


class InventoryNotificationScheduler(models.TransientModel):
    _name = 'inventory.notification.scheduler'



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


    def pick_notification_for_customer(self,picking):
        Stock_Moves = self.env['stock.move'].search([('picking_id','=',picking.id)])
        super_user = self.env['res.users'].search([('id', '=', SUPERUSER_ID), ])
        users = self.env['res.users'].search([('active','=',True),('id','=', picking.sale_id.user_id.id)])
        sales_order=[]
        for stock_move in Stock_Moves:
            sale_order={
                  'sales_order':picking.sale_id.name,
                  'sku':stock_move.product_id.product_tmpl_id.default_code,
                  'Product':stock_move.product_id.name,
                  'qty':stock_move.product_qty
            }
            sales_order.append(sale_order)
        vals = {
            'sale_order_lines': sales_order,
            'subject': "Picking Done For Sale Order # "+picking.sale_id.name ,
            'description': "Please find detail for your Sale Order: " + picking.sale_id.name,
            'header': ['SKU','Product','Qty'],
            'columnProps': ['sku', 'Product','qty'],
        }
        self.process_common_email_notification_template(super_user, picking.sale_id.partner_id, vals['subject'], vals['description'], vals['sale_order_lines'],  vals['header'],
                                                            vals['columnProps'])
    def pull_notification_for_user(self,picking):
        Stock_Moves = self.env['stock.move'].search([('picking_id','=',picking.id)])
        super_user = self.env['res.users'].search([('id', '=', SUPERUSER_ID), ])
        users = self.env['res.users'].search([('active','=',True),('id','=', picking.sale_id.user_id.id)])
        sales_order=[]
        for stock_move in Stock_Moves:
            sale_order={
                  'sales_order':picking.sale_id.name,
                  'sku':stock_move.product_id.product_tmpl_id.default_code,
                  'Product':stock_move.product_id.name,
                  'qty':stock_move.product_qty
            }
            sales_order.append(sale_order)
        vals = {
            'sale_order_lines': sales_order,
            'subject': "Pull Done For Sale Order # "+picking.sale_id.name ,
            'description': "Please find detail Of Sale Order: " + picking.sale_id.name,
            'header': ['SKU','Product','Qty'],
            'columnProps': ['sku', 'Product','qty'],
        }
        for user in users:
            has_group = user.has_group('stock.group_stock_manager')
            if has_group:
                self.process_common_email_notification_template(super_user, user, vals['subject'], vals['description'], vals['sale_order_lines'],  vals['header'],
                                                            vals['columnProps'])
    def pick_notification_for_user(self,picking):
        Stock_Moves = self.env['stock.move'].search([('picking_id','=',picking.id)])
        super_user = self.env['res.users'].search([('id', '=', SUPERUSER_ID), ])
        users = self.env['res.users'].search([('active','=',True),('id','=', picking.sale_id.user_id.id)])
        sales_order=[]
        for stock_move in Stock_Moves:
            sale_order={
                  'sales_order':picking.sale_id.name,
                  'sku':stock_move.product_id.product_tmpl_id.default_code,
                  'Product':stock_move.product_id.name,
                  'qty':stock_move.product_qty
            }
            sales_order.append(sale_order)
        vals = {
            'sale_order_lines': sales_order,
            'subject': "Pick Done For Sale Order # "+picking.sale_id.name ,
            'description': "Please find detail Of Sale Order: " + picking.sale_id.name,
            'header': ['SKU','Product','Qty'],
            'columnProps': ['sku', 'Product','qty'],
        }
        for user in users:
            has_group = user.has_group('stock.group_stock_manager')
            if has_group:
                self.process_common_email_notification_template(super_user, user, vals['subject'], vals['description'], vals['sale_order_lines'],  vals['header'],
                                                            vals['columnProps'])
    def out_notification_for_sale(self,picking):
        Stock_Moves = self.env['stock.move'].search([('picking_id','=',picking.id)])
        super_user = self.env['res.users'].search([('id', '=', SUPERUSER_ID), ])
        users = self.env['res.users'].search([('active','=',True),('id','=', picking.sale_id.user_id.id)])
        sales_order=[]
        for stock_move in Stock_Moves:
            sale_order={
                  'sales_order':picking.sale_id.name,
                  'sku':stock_move.product_id.product_tmpl_id.default_code,
                  'Product':stock_move.product_id.name,
                  'qty':stock_move.product_qty
            }
            sales_order.append(sale_order)
        if picking.carrier_tracking_ref:
            tracking=str(picking.carrier_tracking_ref)
        else:
            tracking=""
        if picking.sale_id and picking.sale_id.partner_id and picking.sale_id.partner_id.name:
            partner_name=picking.sale_id.partner_id.name
        else:
            partner_name=""
        vals = {
            'sale_order_lines': sales_order,
            'subject': "Sale Order # "+picking.sale_id.name+" is Out for Delivery for customer " + partner_name  ,
            'description': "Please find detail Of Sale Order: " + picking.sale_id.name+" and their tracking is "+tracking ,
            'header': ['SKU','Product','Qty'],
            'columnProps': ['sku', 'Product','qty'],
        }
        self.process_common_email_notification_template(super_user, picking.sale_id.user_id, vals['subject'], vals['description'], vals['sale_order_lines'],  vals['header'],
                                                            vals['columnProps'])

    def process_in_stock_scheduler(self):
        _logger.info("process_in_stock_scheduler called")
        product_list=[]
        today_date = date.today()
        today_start = fields.Date.to_string(today_date)
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        dayNumber = today_date.weekday()
        weekday = days[dayNumber]
        customers = self.env['res.partner'].search([('customer', '=', True),('is_parent','=',True),('active', '=', True),(weekday,'=',True),('start_date','<=',today_start),('end_date','>=',today_start)])
        super_user = self.env['res.users'].search([('id', '=', SUPERUSER_ID), ])
        for customr in customers:
            _logger.info("customer :%r", customr)
            custmrs=[]
            cust_ids=[]
            custmrs.append(customr)
            cust_ids.append(customr.id)
            if customr.child_ids:
                custmrs.extend(list(customr.child_ids))
                cust_ids.extend(list(customr.child_ids.ids))
            if(customr.historic_months>0):
                historic_day=customr.historic_months*30
                _logger.info("historic_day :%r", historic_day)
                print('historic_day')
                print(historic_day)
            else:
                historic_day=2
            _logger.info("historic_day :%r", historic_day)
            last_day = fields.Date.to_string(datetime.now() - timedelta(days=historic_day))
            _logger.info("date order  :%r", last_day)
            sales = self.env['sale.order'].search([('partner_id', 'in', cust_ids),('date_order', '>', last_day)])
            _logger.info("sales  :%r", sales)
            products={}
            for sale in sales:
                sale_order_lines = self.env['sale.order.line'].search([('order_id.id', '=', sale.id)])
                for line in sale_order_lines:
                    _logger.info(" product_id qty_available %r",line.product_id.qty_available)
                    if line.product_id.qty_available and line.product_id.qty_available is not None and line.product_id.qty_available > 0:
                        products[line.product_id.id]=line.product_id
            subject = "Products In Stock"
            descrption = "Please find below the items which are back in stock now ! Please find the Website URL: https:/Sps.com."
            header = ['SKU Code','Manufacturer', 'Name','Sales Price','Qty On Hand','Min Expiration Date','Max Expiration Date','Unit Of Measure']
            columnProps = ['sku_code','product_brand_id.name', 'name','list_price','qty_available', 'minExDate', 'maxExDate','uom_id.name']
            if products:
                product_list.extend(list(products.values()))
                for cust in custmrs:
                    self.process_common_email_notification_template(super_user, cust, subject, descrption, product_list,
                                                            header, columnProps,is_employee=False)



    def process_new_product_scheduler(self):
        today_date = datetime.now() - timedelta(days=1)
        today_start = datetime.strftime(today_date, "%Y-%m-%d 00:00:00")
        products = self.env['product.product'].search(
            [('create_date', '>=', today_start), ('notification_date', '=', None),('product_tmpl_id.type','=','product')])
        subject = "New Product In Inventory"
        descrption = "Please find below list of all the new product added in SPS Inventory"
        header=['SKU Code','Name','Sales Price','Cost','Product Type','Min Expiration Date','Max Expiration Date','Qty On Hand','Forecasted Quantity','Unit Of Measure']
        columnProps=['sku_code','product_name','sale_price','standard_price','product_type','minExpDate','maxExpDate','qty_on_hand','forecasted_qty','unit_of_measure']
        self.process_common_product_scheduler(subject, descrption, products, header, columnProps)

    def process_packing_list(self):
        today_date = date.today()
        today_start = datetime.now().date()
        final_date = datetime.strftime(today_start, "%Y-%m-%d 00:00:00")
        last_day = fields.Date.to_string(datetime.now() - timedelta(days=2))
        pull_location_id = self.env['stock.location'].search([('name', '=', 'Pull Zone')]).id
        if not pull_location_id or pull_location_id is None:
            pull_location_id = self.env['stock.location'].search([('name', '=', 'Packing Zone')]).id
        picking = self.env['stock.picking'].search([('sale_id.state', '=', 'sale'),('state', '=', 'done'),('date_done','>=',last_day),('location_dest_id','=',pull_location_id)])
        _logger.info("picking:%r", picking)
        vals={
             'picking_list':picking,
            'custom_template':"inventory_notification.inventory_packing_list_notification"
        }
        if len(picking)>0:
            self.process_packing_email_notification(vals)

            # final_date = fields.Datetime.from_string(today_start)
        products = self.env['product.product'].search([('stock_move_ids.sale_line_id', '!=', False),
                                                       ('stock_move_ids.state', '=', 'done'),
                                                       ('stock_move_ids.picking_id','!=',False),
                                                       ('stock_move_ids.move_line_ids.state', '=', 'done'),
                                                       ('stock_move_ids.move_line_ids.write_date', '>=', last_day),
                                                       ('stock_move_ids.move_line_ids.write_date', '<', final_date),
                                                       ('stock_move_ids.move_line_ids.qty_done', '>', 0),
                                                       ('stock_move_ids.move_line_ids.lot_id', '!=', None)
                                                       ])
        self.process_notification_for_product_red_status(products)


    def process_on_hold_customer(self):
        customers = self.env['res.partner'].search([('on_hold', '=', True),('is_parent','=',True)])
        super_user = self.env['res.users'].search([('id', '=', SUPERUSER_ID), ])
        users = self.env['res.users'].search([('active','=',True)])
        for customer in customers:
            _logger.info("customer :%r", customer)
        if customers:
            for user in users:
                has_group = user.has_group('stock.group_stock_manager') or user.has_group('sales_team.group_sale_manager')
                if has_group:
                    _logger.info("customer :%r",user)
                    columnProps=['name','user_id.display_name']
                    header=['Serial Number','Customer Name', 'Sales Person']
                    email_form=super_user
                    email_to=user
                    subject='Customer On Hold'
                    description='Please find below the list of customers whose "On-hold status" has been released from Accounting Department.'
                    self.process_common_email_notification_template(email_form,email_to,subject,description,customers,header,columnProps)


    def process_hold_off_customer(self,partner_id):
        sales = self.env['sale.order'].search([('state', '=', 'sale'),('partner_id', '=', partner_id.id)])
        super_user = self.env['res.users'].search([('id', '=', SUPERUSER_ID), ])
        users = self.env['res.users'].search([('active','=',True)])
        sales_order=[]
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
                sale_order={
                    'sales_order':sale.name,
                    'shipping_address':shipping_address
                }
                sales_order.append(sale_order)
        if sales:
            vals = {
                'sale_order_lines': sales_order,
                'subject': "shipment need to release for "+partner_id.display_name  ,
                'description': "Please release the shipment of customer: " + partner_id.display_name ,
                'header': ['Sales order', 'Shipping Address'],
                'columnProps': ['sales_order', 'shipping_address'],
            }
            for user in users:
                has_group = user.has_group('stock.group_stock_manager')
                if has_group:
                    self.process_common_email_notification_template(super_user, user, vals['subject'], vals['description'],  vals['sale_order_lines'],  vals['header'],
                                                                vals['columnProps'])

    def process_notification_for_product_red_status(self,products):
        super_user = self.env['res.users'].search([('id', '=', SUPERUSER_ID), ])
        users = self.env['res.users'].search([('active','=',True)])
        green_products=[]
        yellow_products=[]
        red_product=[]
        switcher = {
            'product': "Stockable",
            'consu': "Consumable",
            'service': "Service"
        }
        for product in products:
            vals = {
                'sku_code':self.check_isAvailable(product.product_tmpl_id.sku_code),
                'sale_price': product.lst_price,
                'standard_price': product.product_tmpl_id.standard_price,
                'product_type': switcher.get(product.type, " "),
                'qty_on_hand': product.qty_available,
                'forecasted_qty': product.virtual_available,
                'product_name': self.check_isAvailable_product_code(product.default_code)+" "+product.product_tmpl_id.name,
                'unit_of_measure': product.product_tmpl_id.uom_id.name
            }

            if  product.inventory_percent_color > 75 and  product.inventory_percent_color <=125:
                yellow_products.append(vals)
            elif product.inventory_percent_color <= 75:
                red_product.append(vals)

        for user in users:
            has_group = user.has_group('purchase.group_purchase_manager') or user.has_group(
                'sales_team.group_sale_manager')
            if has_group:
                if yellow_products:
                    self.process_notify_yellow_product(yellow_products,user,super_user)
                if red_product:
                    self.process_notify_red_product(red_product,user,super_user)

    def process_notification_for_product_green_status(self,products):
        super_user = self.env['res.users'].search([('id', '=', SUPERUSER_ID), ])
        users = self.env['res.users'].search([('active','=',True)])
        green_products=[]
        yellow_products=[]
        red_product=[]
        switcher = {
            'product': "Stockable",
            'consu': "Consumable",
            'service': "Service"
        }
        for product in products:
            vals = {
                'sku_code':self.check_isAvailable(product.product_tmpl_id.sku_code),
                'sale_price': product.lst_price,
                'standard_price': product.product_tmpl_id.standard_price,
                'product_type': switcher.get(product.type, " "),
                'qty_on_hand': product.qty_available,
                'forecasted_qty': product.virtual_available,
                'product_name': self.check_isAvailable_product_code(product.default_code)+" "+product.product_tmpl_id.name,
                'unit_of_measure': product.product_tmpl_id.uom_id.name
            }
            if product.inventory_percent_color > 125:
                green_products.append(vals)

        for user in users:
            has_group = user.has_group('purchase.group_purchase_manager') or user.has_group(
                'sales_team.group_sale_manager')
            if has_group:
                if green_products:
                    self.process_notify_green_product(green_products,user,super_user)
                if yellow_products:
                    self.process_notify_yellow_product(yellow_products,user,super_user)

    def process_notification_for_in_stock_report(self,products):
        _logger.info("process_notification_for_in_stock_report called....")
        today_date = date.today()
        today_start = fields.Date.to_string(today_date)
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        dayNumber = today_date.weekday()
        weekday=days[dayNumber]
        super_user = self.env['res.users'].search([('id', '=', SUPERUSER_ID), ])
        _logger.info("weekday: %r", weekday)
        custmer_user=self.env['res.users'].search([('partner_id.customer', '=', True),('active','=',True) ])
        for customer in custmer_user:
         user = self.env['res.partner'].search([(weekday,'=',True),('customer','=',True),('start_date','<=',today_start),('end_date','>=',today_start),('id','=',customer.partner_id.id)])
         if user and products:
                _logger.info("user:%r ",user)
                subject = "In Stock Product"
                description = "Please find below list of all the product whose are in stock in SPS Inventory."
                header = ['Manufacturer', 'Sku Reference', 'Product Code', 'Product Name', 'Qty In Stock',
                          'Product Price', 'Min Expiration Date', 'Max Expiration Date']
                columnProps = ['manufacturer', 'sku_reference', 'product_code', 'product_name', 'qty_available',
                               'product_price_symbol', 'minExDate', 'maxExDate']
                self.process_common_email_notification_template(super_user, user,  subject,
                                                            description, products, header, columnProps)




    def process_notify_green_product(self,products,to_user,from_user):
        subject = "products which are in green status"
        description = "Please find below list of all the product whose status in Color(Green) in SPS Inventory."
        header = ['SKU Code','Name', 'Sales Price', 'Cost', 'Product Type',
                  'Qty On Hand', 'Forecasted Quantity', 'Unit Of Measure']
        columnProps = ['sku_code','product_name', 'sale_price', 'standard_price', 'product_type',
                       'qty_on_hand', 'forecasted_qty', 'unit_of_measure']
        self.process_common_email_notification_template(from_user, to_user, subject,
                                                        description, products, header, columnProps)


    def process_notify_yellow_product(self, products,to_user,from_user):
        subject = "products which are in yellow status"
        description = "Please find below list of all the product whose status in Color(Yellow) in SPS Inventory."
        header = ['SKU Code', 'Name', 'Sales Price', 'Cost', 'Product Type',
                  'Qty On Hand', 'Forecasted Quantity', 'Unit Of Measure']
        columnProps = ['sku_code', 'product_name', 'sale_price', 'standard_price', 'product_type',
                       'qty_on_hand', 'forecasted_qty', 'unit_of_measure']
        self.process_common_email_notification_template(from_user, to_user, subject,
                                                        description, products, header, columnProps)


    def process_notify_red_product(self, products,to_user,from_user):
        subject = "products which are in red status"
        description = "Please find below list of all the product whose status in Color(Red) in SPS Inventory."
        header = ['SKU Code', 'Name', 'Sales Price', 'Cost', 'Product Type',
                  'Qty On Hand', 'Forecasted Quantity', 'Unit Of Measure']
        columnProps = ['sku_code', 'product_name', 'sale_price', 'standard_price', 'product_type',
                       'qty_on_hand', 'forecasted_qty', 'unit_of_measure']
        self.process_common_email_notification_template(from_user, to_user, subject,
                                                        description, products, header, columnProps)


    def process_notify_available(self):
        today_date = date.today()
        today_start = fields.Date.to_string(today_date)
        last_day = fields.Date.to_string(datetime.now() - timedelta(days=1))
        quant = self.env['stock.quant'].search(
            [('create_date', '>=', last_day), ('quantity', '>', 0),('product_tmpl_id.notify', '=', True),])
        products = quant.mapped('product_id')
        subject = "Products Back In Stock"
        descrption = "Please find below the list items which are back in stock now in SPS Inventory."
        header = ['SKU Code','Name', 'Sales Price', 'Cost', 'Product Type', 'Min Expiration Date', 'Max Expiration Date',
                  'Qty On Hand', 'Forecasted Quantity', 'Unit Of Measure']
        columnProps = ['sku_code','product_name', 'sale_price', 'standard_price', 'product_type', 'minExDate', 'maxExDate',
                       'qty_on_hand', 'forecasted_qty', 'unit_of_measure']
        self.process_common_product_scheduler(subject, descrption, products, header, columnProps)
        quant = self.env['stock.quant'].search(
            [('write_date', '>=', last_day), ('quantity', '>', 0), ])
        products = quant.mapped('product_id')
        self.process_notification_for_product_green_status(products)



    def process_packing_email_notification(self,vals):
        super_user = self.env['res.users'].search([('id', '=', SUPERUSER_ID), ])
        users = self.env['res.users'].search([('active','=',True)])
        template = self.env.ref(vals['custom_template'])
        for user in users:
            has_group = user.has_group('stock.group_stock_manager')
            if has_group:
                local_context = {'picking_list': vals['picking_list'],
                                 'subject': 'New Sales Order',
                         'email_from': super_user.email, 'email_to': user.email,
                }
                html_file = self.env['inventory.notification.html'].search([])
                finalHTML = html_file.process_packing_list_html(vals['picking_list'])
                template.with_context(local_context).send_mail(SUPERUSER_ID, raise_exception=True, force_send=True, )
                mail = self.env["mail.thread"]
                mail.message_post(
                     body=finalHTML,
                     subject='New Sales Order',
                     message_type='notification',
                     partner_ids=[user.partner_id.id],
                     content_subtype='html'
                 )



    def process_common_email_notification_template(self, email_from_user, email_to_user, subject, descrption, products, header, columnProps,custom_template="inventory_notification.common_mail_template",is_employee=True):
        template = self.env.ref(custom_template)
        product_dict = {}
        product_list = []
        coln_name = []
        serial_number=0
        background_color = "#f0f8ff"
        for product in products:
            coln_name = []
            query_result = False
            if header[0]== 'Serial Number':
                product_dict['Serial Number'] =serial_number+1
                coln_name.append('Serial Number')
            if background_color == "#ffffff":
                background_color = "#f0f8ff"
            else:
                background_color = "#ffffff"
            if hasattr(product,'id'):
                stock_warehouse_id = self.env['stock.warehouse'].search([('id', '=', 1), ])
                stock_location_id = self.env['stock.location'].search([('id', '=', stock_warehouse_id.lot_stock_id.id),])
                if stock_location_id:
                    self.env.cr.execute(
                        "SELECT  min(use_date), max (use_date) FROM stock_production_lot spl LEFT JOIN   stock_quant sq ON sq.lot_id=spl.id LEFT JOIN  stock_location sl ON sl.id=sq.location_id   where sl.id = %s and  sq.product_id = %s",
                        (stock_location_id.id,product['id'],))
                    query_result = self.env.cr.dictfetchone()
            for column_name in columnProps:
                coln_name.append(column_name)
                if column_name == 'minExDate':
                    if query_result and query_result['min']:
                        column = datetime.strptime(query_result['min'], "%Y-%m-%d %H:%M:%S")
                    else:
                        column=""
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
                                    column = column[lst[col]]
                            else:
                                column = column[lst]
                if column:
                    product_dict[column_name] = column
                else:
                    product_dict[column_name] = ""
            product_dict['background_color'] = background_color
            product_list.append(product_dict)
            product_dict = {}
        #print(products)
        if products:
            vals={
                'product_list':product_list,
                'headers':header,
                'coln_name':coln_name,
                'email_from_user':email_from_user,
                'email_to_user':email_to_user,
                'subject':subject,
                'description':descrption,
                'template':template,
                'is_employee': is_employee
            }
            self.send_email_and_notification(vals)



    def send_email_and_notification(self,vals):
        local_context = {'products': vals['product_list'], 'headers': vals['headers'], 'columnProps': vals['coln_name'],
                         'email_from': vals['email_from_user'].email, 'email_to': vals['email_to_user'].email, 'subject': vals['subject'],
                         'descrption': vals['description']}
        html_file = self.env['inventory.notification.html'].search([])
        finalHTML = html_file.process_common_html(vals['subject'], vals['description'], vals['product_list'], vals['headers'], vals['coln_name'])
        #print(finalHTML)
        if hasattr(vals['email_to_user'],'partner_ids'):
            partner_ids=[vals['email_to_user'].partner_ids.id]
        else:
            partner_ids = [vals['email_to_user'].id]
        try:
            if vals['email_to_user'].email:
                template_id = vals['template'].with_context(local_context).send_mail(SUPERUSER_ID, raise_exception=True, force_send=True, )
        except:
            erro_msg="mail sending fail for email id: %r" + vals['email_to_user'].email +" sending error report to admin"
            _logger.info(erro_msg)
            print("mail sending fail for email id: " + vals['email_to_user'].email +" sending error report to admin")
            subject= "mail send fail for user "+ vals['email_to_user'].email + " (Subject: "+vals['subject']
            cache_context = {'products': vals['product_list'], 'headers': vals['headers'],
                             'columnProps': vals['coln_name'],
                             'email_from': vals['email_from_user'].email, 'email_to': vals['email_from_user'].email,
                             'subject': subject,
                             'descrption': vals['description']}
            try:
                vals['template'].with_context(cache_context).send_mail(SUPERUSER_ID, raise_exception=True,force_send=True)
                vals['template'].with_context(local_context).send_mail(SUPERUSER_ID, raise_exception=True)
            except:
                _logger.info("mail sending fail for email id: %r" , vals['email_to_user'].email)
                print("mail sending fail for email id: " + vals['email_to_user'].email)

        if vals['is_employee']:
            mail = self.env["mail.thread"]
            mail.message_post(
                body=finalHTML,
                subject=vals['subject'],
                message_type='notification',
                partner_ids=partner_ids,
                content_subtype='html'
            )

        # mail = self.env['mail.mail'].browse(template_id)
        # attachment_value = {
        #     'name': 'product status',
        #     'res_name': "red product status",
        #     'res_model': 'product.product',
        #     'type': 'binary',
        #     'res_id': self.ids[0],
        #     'datas': base64.b64encode(mail.body_html.encode("utf-8")),
        #     'datas_fname': 'product_status' + '.pdf',
        # }
        # new_attachment = self.env['ir.attachment'].create(attachment_value)
        # mail.attachment_ids |= new_attachment
        # mail.send()



    def process_common_product_scheduler(self,subject,descrption,products, header, columnProps):
        super_user=self.env['res.users'].search([('id', '=',SUPERUSER_ID),])
        users = self.env['res.users'].search([('active','=',True)])
        today_date = date.today()
        today_start = fields.Date.to_string(today_date)
        switcher = {
            'product': "Stockable",
            'consu': "Consumable",
            'service': "Service"
        }
        if len(products)>0:
            stock_warehouse_id = self.env['stock.warehouse'].search([('id', '=', 1), ])
            stock_location_id = self.env['stock.location'].search([('id', '=', stock_warehouse_id.lot_stock_id.id), ])
            for user in users:
                has_group = user.has_group('sales_team.group_sale_manager')
                if has_group:
                    product_list=[]
                    row = "even"
                    for product in products:
                        query_result = False
                        if row=='even':
                            background_color = "#ffffff"
                            row="odd"
                        else:
                            background_color = "#f0f8ff"
                            row = "even"
                        qty_on_hand=product.qty_available
                        forecasted_qty=product.virtual_available
                        if stock_location_id:
                            self.env.cr.execute(
                                "SELECT  min(use_date), max (use_date) FROM stock_production_lot spl LEFT JOIN   stock_quant sq ON sq.lot_id=spl.id LEFT JOIN  stock_location sl ON sl.id=sq.location_id   where sl.id = %s and  sq.product_id = %s",
                                (stock_location_id.id, product.id,))
                            query_result = self.env.cr.dictfetchone()
                        if query_result and query_result['min']:
                            minExDate = datetime.strptime(query_result['min'], "%Y-%m-%d %H:%M:%S")
                        else:
                            minExDate = ""
                        if query_result and query_result['max']:
                            maxExDate = datetime.strptime(query_result['max'], "%Y-%m-%d %H:%M:%S")
                        else:
                            maxExDate = ""
                        vals={
                            'minExpDate':minExDate,
                            'maxExpDate':maxExDate,
                            'sale_price':product.lst_price,
                            'standard_price':product.product_tmpl_id.standard_price,
                            'product_type':switcher.get(product.type, " "),
                            'qty_on_hand':qty_on_hand,
                            'forecasted_qty':forecasted_qty,
                            'background_color':background_color,
                            'product_name':product.product_tmpl_id.name,
                            'sku_code':product.product_tmpl_id.sku_code,
                            'unit_of_measure':product.product_tmpl_id.uom_id.name
                        }
                        product_list.append(vals)
                        product.write({'notification_date': today_start})
                    self.process_common_email_notification_template(super_user, user, subject,
                                                               descrption, product_list, header, columnProps)

    def check_isAvailable(self, value):
        if value:
            return str(value)
        return ""

    def check_isAvailable_product_code(self,value):
        if value:
            return "["+str(value)+"]"
        return ""
