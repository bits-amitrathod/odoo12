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
        product_lots = self.env['stock.production.lot'].search([])
        for product_lot in product_lots:
            _logger.info("product_lot:%r", product_lot)
        self.process_notification_scheduler()


    @api.model
    @api.multi
    def process_notification_scheduler(self):
        _logger.info("process_notification_scheduler called")
        self.process_new_product_scheduler()
        self.process_notify_available()
        self.process_packing_list()
        self.process_on_hold_customer()


    def process_new_product_scheduler(self):
        today_date = date.today()
        today_start = fields.Date.to_string(today_date)
        products = self.env['product.product'].search(
            [('create_date', '>=', today_start), ('notification_date', '=', None)])
        subject = "New Product In Inventory"
        descrption = "Please find below list of all the new product added in SPS Inventory"
        header=['SKU Code','Name','Sales Price','Cost','Product Type','Min Expiration Date','Max Expiration Date','Qty On Hand','Forecasted Quantity','Unit Of Measure']
        columnProps=['sku_code','product_name','sale_price','standard_price','product_type','minExDate','maxExDate','qty_on_hand','forecasted_qty','unit_of_measure']
        self.process_common_product_scheduler(subject, descrption, products, header, columnProps)

    def process_packing_list(self):
        today_date = date.today()
        today_start = datetime.now().date()
        final_date = datetime.strftime(today_start, "%Y-%m-%d 00:00:00")
        last_day = fields.Date.to_string(datetime.now() - timedelta(days=1))
        picking = self.env['stock.picking'].search([('sale_id', '!=', False),('state', '=', 'done'),('write_date','>=',last_day),('write_date', '<', final_date)])
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
        self.process_notification_for_in_stock_report(products)



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



    def process_common_email_notification_template(self, email_from_user, email_to_user, subject, descrption, products, header, columnProps,custom_template="inventory_notification.common_mail_template"):
        template = self.env.ref(custom_template)
        product_dict = {}
        product_list = []
        coln_name = []
        serial_number=0
        background_color = "#f0f8ff"
        for product in products:
            coln_name = []
            if header[0]== 'Serial Number':
                product_dict['Serial Number'] =serial_number+1
                coln_name.append('Serial Number')
            if background_color == "#ffffff":
                background_color = "#f0f8ff"
            else:
                background_color = "#ffffff"
            for column_name in columnProps:
                coln_name.append(column_name)
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
                product_dict[column_name] = column
            product_dict['background_color'] = background_color
            product_list.append(product_dict)
            product_dict = {}
        if products:
            vals={
                'product_list':product_list,
                'headers':header,
                'coln_name':coln_name,
                'email_from_user':email_from_user,
                'email_to_user':email_to_user,
                'subject':subject,
                'description':descrption,
                'template':template
            }
            self.send_email_and_notification(vals)



    def send_email_and_notification(self,vals):
        local_context = {'products': vals['product_list'], 'headers': vals['headers'], 'columnProps': vals['coln_name'],
                         'email_from': vals['email_from_user'].email, 'email_to': vals['email_to_user'].email, 'subject': vals['subject'],
                         'descrption': vals['description']}
        html_file = self.env['inventory.notification.html'].search([])
        finalHTML = html_file.process_common_html(vals['subject'], vals['description'], vals['product_list'], vals['headers'], vals['coln_name'])
        try:
         template_id = vals['template'].with_context(local_context).send_mail(SUPERUSER_ID, raise_exception=True, force_send=True, )
        except:
            vals['template'].with_context(local_context).send_mail(SUPERUSER_ID, raise_exception=True)
        mail = self.env["mail.thread"]
        mail.message_post(
            body=finalHTML,
            subject=vals['subject'],
            message_type='notification',
            partner_ids=[vals['email_to_user'].partner_id.id],
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
            for user in users:
                has_group = user.has_group('sales_team.group_sale_manager')
                if has_group:
                    product_list=[]
                    row = "even"
                    for product in products:
                        if row=='even':
                            background_color = "#ffffff"
                            row="odd"
                        else:
                            background_color = "#f0f8ff"
                            row = "even"
                        qty_on_hand=product.qty_available
                        forecasted_qty=product.virtual_available

                        self.env.cr.execute(
                            "SELECT  min(use_date), max (use_date) FROM stock_production_lot spl LEFT JOIN   stock_quant sq ON sq.lot_id=spl.id LEFT JOIN  stock_location sl ON sl.id=sq.location_id   where (sl.usage ='internal' OR sl.usage='transit') and  sq.product_id = %s",
                            (product.id,))
                        query_result = self.env.cr.dictfetchone()
                        minExDate = fields.Date.from_string(query_result['min'])
                        maxExDate = fields.Date.from_string(query_result['max'])
                        vals={
                            'minExDate':minExDate,
                            'maxExDate':maxExDate,
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
