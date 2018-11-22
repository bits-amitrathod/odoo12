# -*- coding: utf-8 -*-

from odoo import models, fields, api,SUPERUSER_ID
import logging
import datetime
import base64
from datetime import date
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
        self.process_new_product_scheduler()
        self.process_notify_available()
        self.process_packing_list()
        self.process_on_hold_customer()
        self.process_notification_for_product_status()
        self.process_notification_for_in_stock_report()


    def process_new_product_scheduler(self):
        today_date = date.today()
        today_start = fields.Date.to_string(today_date)
        products = self.env['product.product'].search(
            [('create_date', '>=', today_start), ('notification_date', '=', None)])
        subject = "New Product In Inventory"
        descrption = "Please find below list of all the new product added in SPS Inventory"
        header=['Name','Sales Price','Cost','Product Type','Min Expiration Date','Max Expiration Date','Qty On Hand','Forecasted Quantity','Unit Of Measure']
        columnProps=['product_name','sale_price','standard_price','product_type','maxExDate','maxExDate','qty_on_hand','forecasted_qty','unit_of_measure']
        self.process_common_product_scheduler(subject, descrption, products, header, columnProps)

    def process_packing_list(self):
        today_date = date.today()
        today_start = fields.Date.to_string(today_date)
        users = self.env['res.users'].search([])
        sales = self.env['sale.order'].search([('state','=','sale')])
        for sale in sales:
            sale_order_lines = self.env['sale.order.line'].search([('order_id.id','=',sale.id),
                                                              ('move_ids.state','=','assigned'),
                                                              ('move_ids.move_line_ids.state','=','assigned'),
                                                              ('move_ids.move_line_ids.write_date','>=',today_start),
                                                              ('move_ids.move_line_ids.qty_done','>',0),
                                                              ('move_ids.move_line_ids.lot_id','!=',None)])

            shipping_address=self.check_isAvailable(sale.partner_id.street) + " " + self.check_isAvailable(sale.partner_id.street2) + " "\
                             +self.check_isAvailable(sale.partner_id.zip) + " "+ self.check_isAvailable(sale.partner_id.city)+" "+ \
                             self.check_isAvailable(sale.partner_id.state_id.name) + " "+ self.check_isAvailable(sale.partner_id.country_id.name)
            vals={
                'sale_order_lines':sale_order_lines,
                'subject':"New Sale Order",
                'descrption':"Please find below Packing list for Order No:" + sale.name +" Dated:"+ today_start,
                'header': ['Name',  'Lot No#', 'Expiration Date','Qty On Hand', 'Unit Of Measure'],
                'columnProps':['name',  'move_ids.move_line_ids.lot_id.name', 'move_ids.move_line_ids.lot_id.use_date',
                           'product_id.qty_available',  'product_id.product_tmpl_id.uom_id.name'],
                'customer_name':self.check_isAvailable(sale.partner_id.display_name),
                'shipping_address':shipping_address,
                'customer_po_no': self.check_isAvailable(sale.client_order_ref),
                'carrier_name': self.check_isAvailable(sale.carrier_info),
                'carrier_acc_no':  self.check_isAvailable(sale.carrier_acc_no),
                'custom_template':"inventory_notification.inventory_packing_list_notification"
            }
            if len(sale_order_lines)>0:
                self.process_packing_email_notification(vals)

    def process_on_hold_customer(self):
        customers = self.env['res.partner'].search([('on_hold', '=', True),('is_parent','=',True)])
        super_user = self.env['res.users'].search([('id', '=', SUPERUSER_ID), ])
        users = self.env['res.users'].search([])
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
        sales = self.env['sale.order'].search([('state', '=', 'sale'),('partner_id', '=', partner_id)])
        super_user = self.env['res.users'].search([('id', '=', SUPERUSER_ID), ])
        users = self.env['res.users'].search([])
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
        vals = {
            'sale_order_lines': sales_order,
            'subject': "shipment need to release for "+sale.partner_id.display_name  ,
            'description': "Please release the shipment of customer: " + sale.partner_id.display_name ,
            'header': ['Sales order', 'Shipping Address'],
            'columnProps': ['sales_order', 'shipping_address'],
        }
        for user in users:
            has_group = user.has_group('stock.group_stock_manager')
            if has_group:
                self.process_common_email_notification_template(super_user, user, vals['subject'], vals['description'],  vals['sale_order_lines'],  vals['header'],
                                                            vals['columnProps'])

    def process_notification_for_product_status(self):
        products=self.env['product.product'].search([('product_tmpl_id.type','=','product')])
        super_user = self.env['res.users'].search([('id', '=', SUPERUSER_ID), ])
        users = self.env['res.users'].search([])
        location_ids = self.env['stock.location'].search([('usage', '=', 'internal'), ('active', '=', True)])
        green_products=[]
        yellow_products=[]
        red_product=[]
        switcher = {
            'product': "Stockable",
            'consu': "Consumable",
            'service': "Service"
        }
        for product in products:
            product.product_tmpl_id._compute_max_inventory_level()
            vals = {
                'sku_code':self.check_isAvailable(product.product_tmpl_id.sku_code),
                'sale_price': product.lst_price,
                'standard_price': product.product_tmpl_id.standard_price,
                'product_type': switcher.get(product.type, " "),
                'qty_on_hand': product.product_tmpl_id.qty_in_stock,
                'forecasted_qty': product.virtual_available,
                'product_name': self.check_isAvailable_product_code(product.default_code)+" "+product.product_tmpl_id.name,
                'unit_of_measure': product.product_tmpl_id.uom_id.name
            }
            if product.inventory_percent_color > 125:
                green_products.append(vals)
            elif  product.inventory_percent_color > 75 and  product.inventory_percent_color <=125:
                yellow_products.append(vals)
            elif product.inventory_percent_color <= 75:
                red_product.append(vals)

        for user in users:
            has_group = user.has_group('purchase.group_purchase_manager') or user.has_group(
                'sales_team.group_sale_manager')
            if has_group:
                if green_products:
                    self.process_notify_green_product(green_products,user,super_user)
                if yellow_products:
                    self.process_notify_yellow_product(yellow_products,user,super_user)
                if red_product:
                    self.process_notify_red_product(red_product,user,super_user)


    def process_notification_for_in_stock_report(self):
        today_date = date.today()
        today_start = fields.Date.to_string(today_date)
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        dayNumber = today_date.weekday()
        weekday=days[dayNumber]
        super_user = self.env['res.users'].search([('id', '=', SUPERUSER_ID), ])
        _logger.info("weekday: %r", weekday)
        users = self.env['res.partner'].search([(weekday,'=',True),('customer','=',True),('start_date','<=',today_start),('end_date','>=',today_start)])
        products= self.env['product.product'].search([('product_tmpl_id.type','=','product')])
        if products:
            products._compute_max_inventory_level()
            for user in users:
                _logger.info("user:%r ",user)
                subject = "In Stock Product"
                description = "Please find below list of all the product whose are in stock in SPS Inventory."
                header = ['Manufacturer', 'Sku Reference', 'Product Code', 'Product Name', 'Qty In Stock',
                          'Product Price', 'Min Expiration Date', 'Max Expiration Date']
                columnProps = ['manufacturer', 'sku_reference', 'product_code', 'product_name', 'qty_in_stock',
                               'product_price_symbol', 'minExDate', 'maxExDate']
                self.process_common_email_notification_template(user, super_user, subject,
                                                            description, products, header, columnProps)



    def process_notify_green_product(self,products,to_user,from_user):
        subject = "products which are in green status"
        description = "Please find below list of all the product whose status in Color(Green) in SPS Inventory."
        header = ['SKU','Name', 'Sales Price', 'Cost', 'Product Type',
                  'Qty On Hand', 'Forecasted Quantity', 'Unit Of Measure']
        columnProps = ['sku_code','product_name', 'sale_price', 'standard_price', 'product_type',
                       'qty_on_hand', 'forecasted_qty', 'unit_of_measure']
        self.process_common_email_notification_template(from_user, to_user, subject,
                                                        description, products, header, columnProps)


    def process_notify_yellow_product(self, products,to_user,from_user):
        subject = "products which are in yellow status"
        description = "Please find below list of all the product whose status in Color(Yellow) in SPS Inventory."
        header = ['SKU', 'Name', 'Sales Price', 'Cost', 'Product Type',
                  'Qty On Hand', 'Forecasted Quantity', 'Unit Of Measure']
        columnProps = ['sku_code', 'product_name', 'sale_price', 'standard_price', 'product_type',
                       'qty_on_hand', 'forecasted_qty', 'unit_of_measure']
        self.process_common_email_notification_template(from_user, to_user, subject,
                                                        description, products, header, columnProps)


    def process_notify_red_product(self, products,to_user,from_user):
        subject = "products which are in red status"
        description = "Please find below list of all the product whose status in Color(Red) in SPS Inventory."
        header = ['SKU', 'Name', 'Sales Price', 'Cost', 'Product Type',
                  'Qty On Hand', 'Forecasted Quantity', 'Unit Of Measure']
        columnProps = ['sku_code', 'product_name', 'sale_price', 'standard_price', 'product_type',
                       'qty_on_hand', 'forecasted_qty', 'unit_of_measure']
        self.process_common_email_notification_template(from_user, to_user, subject,
                                                        description, products, header, columnProps)


    def process_notify_available(self):
        today_date = date.today()
        today_start = fields.Date.to_string(today_date)
        quant = self.env['stock.quant'].search(
            [('write_date', '>=', today_start), ('quantity', '>', 0),('product_tmpl_id.notify', '=', True),])
        products = quant.mapped('product_id')
        subject = "Products Back In Stock"
        descrption = "<p>Please find below the list items which are back in stock now in SPS Inventory.</p>"
        header = ['Name', 'Sales Price', 'Cost', 'Product Type', 'Min Expiration Date', 'Max Expiration Date',
                  'Qty On Hand', 'Forecasted Quantity', 'Unit Of Measure']
        columnProps = ['product_name', 'sale_price', 'standard_price', 'product_type', 'maxExDate', 'maxExDate',
                       'qty_on_hand', 'forecasted_qty', 'unit_of_measure']
        self.process_common_product_scheduler(subject, descrption, products, header, columnProps)



    def process_packing_email_notification(self,vals):
        super_user = self.env['res.users'].search([('id', '=', SUPERUSER_ID), ])
        users = self.env['res.users'].search([])
        template = self.env.ref(vals['custom_template'])
        product_dict = {}
        product_list = []
        coln_name = []
        background_color = "#ffffff"
        for product in vals['sale_order_lines']:
            coln_name = []
            if background_color == "#ffffff":
                background_color = "#f0f8ff"
            else:
                background_color = "#ffffff"
            for column_name in vals['columnProps']:
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
                                pri_col=""
                                for cols in column:
                                  cols = cols[lst[col]]
                                  pri_col=cols
                                column=pri_col
                        else:
                            column = column[lst]
                product_dict[column_name] = column
            product_dict['background_color'] = background_color
            product_list.append(product_dict)
            product_dict = {}
        for user in users:
            has_group = user.has_group('stock.group_stock_manager')
            if has_group:
                local_context = {'products': product_list, 'headers': vals['header'], 'columnProps': coln_name,
                         'email_from': super_user.email, 'email_to': user.email, 'subject': vals['subject'],
                         'descrption': vals['descrption'],'customer_name':vals['customer_name'],'shipping_address':vals['shipping_address'],
                         'customer_po_no':vals['customer_po_no'],'carrier_name':vals['carrier_name'],'carrier_acc_no':vals['carrier_acc_no']
                }
                html_description="""
                    <div>
                       <p>"""+vals['descrption']+"""</p>
                        <p> <span style = "font-weight: bold;" > 
                            Customer Name: </span >""" +vals['customer_name'] + """ </p >
                        <p> 
                            <span style = "font-weight: bold;" > Shipping Address: </span >""" +vals['shipping_address'] +"""</p>
                         <p> <span style = "font-weight: bold;" > 
                           Customer PO Number: </span >""" +vals['customer_po_no'] + """ </p >
                        <p> 
                            <span style = "font-weight: bold;" > Carrier Name: </span >""" +vals['carrier_name'] +"""</p> 
                        <p> 
                            <span style = "font-weight: bold;" > Carrier Account Number: </span >""" +vals['carrier_acc_no'] +"""</p>       
                    </div>"""
                html_file = self.env['inventory.notification.html'].search([])
                finalHTML = html_file.process_common_html(vals['subject'], html_description, product_list, vals['header'], coln_name)
                template.with_context(local_context).send_mail(SUPERUSER_ID, raise_exception=True, force_send=True, )
                mail = self.env["mail.thread"]
                mail.message_post(
                    body=finalHTML,
                    subject=vals['subject'],
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
        users = self.env['res.users'].search([])
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
                            "SELECT min(use_date), max (use_date) FROM stock_production_lot where product_id = %s",
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