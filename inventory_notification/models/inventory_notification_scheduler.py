# -*- coding: utf-8 -*-

from odoo import models, fields, api,SUPERUSER_ID
import logging
import datetime
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
        # self.process_new_product_scheduler()
        # self.process_notify_available()
        self.process_packing_list()


    def process_new_product_scheduler(self):
        today_date = date.today()
        today_start = fields.Date.to_string(today_date)
        products = self.env['product.product'].search(
            [('create_date', '>=', today_start), ('notification_date', '=', None)])
        subject = "New Product In Inventory"
        descrption = "Please find below list of all the new product added in SPS Inventory"
        self.process_common_product_scheduler(subject, descrption, products)

    def process_packing_list(self):
        sale_orders = self.env['sale.order'].search([('state','=','sale'),])
        for sale_order in sale_orders:
            _logger.info("sale_order :%r",sale_order)
    def process_notify_available(self):
        today_date = date.today()
        today_start = fields.Date.to_string(today_date)
        quant = self.env['stock.quant'].search(
            [('write_date', '>=', today_start), ('quantity', '>', 0)])
        filter_quant=quant.filtered(lambda q: q.product_tmpl_id.notify == True)
        products = filter_quant.mapped('product_id')
        subject = "Products Back In Stock"
        descrption = "Please find below the list items which are back in stock now in SPS Inventory."
        self.process_common_product_scheduler(subject, descrption, products)


    def process_common_product_scheduler(self,subject,descrption,products):
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
                has_group = user.has_group('purchase.group_purchase_manager')
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

                    template = self.env.ref('inventory_notification.mail_template_product_inventory_notification_email')
                    local_context = { 'products': product_list,'email_from':super_user.email,'email_to':user.email,'subject':subject,'descrption':descrption}

                    finalHTML=self.process_common_html(subject, descrption, product_list)
                    if product_list:
                        template.with_context(local_context).send_mail(SUPERUSER_ID, raise_exception=True,force_send=True, )
                        mail = self.env["mail.thread"]
                        mail.message_post(
                            body=finalHTML,
                            subject="New Product In Inventory",
                            message_type='notification',
                            partner_ids=[user.partner_id.id],
                            content_subtype='html'
                        )

    def process_common_html(self,subject,descrption,product_list):
        header = """
                <html>
                 <div style='margin:auto;width:100%;background-color: #ffffff; padding-left: 60px;' class='oe_structure'>
                  <div >
                    <h2>""" +subject+"""</h2>
                    <p>Hi Team,</p>
                    <p>"""+descrption+ """ </p>
                 </div>
                 <div class='row'>  
                 </div>
                <div>
                <table style='border: 1px solid black;width:100%;margin-top:20px'>
                    <thead style='background-color:#D6DBDF;line-height: 30px'>
                        <tr style='border: 1px solid black;'>
                            <th  style='border: 1px solid black;text-align: center;'>  Name </th>
                            <th  style='border: 1px solid black;text-align: center;'> Sales Price </th>
                            <th  style='border: 1px solid black;text-align: center;'> Cost </th>
                            <th  style='border: 1px solid black;text-align: center;'> Product Type </th>
                            <th  style='border: 1px solid black;text-align: center;'> Min Expiration Date </th>
                            <th  style='border: 1px solid black;text-align: center;'> Max Expiration Date </th>
                            <th  style='border: 1px solid black;text-align: center;'> Qty On Hand </th>
                            <th  style='border: 1px solid black;text-align: center;'> Forecasted Quantity </th>
                            <th  style='border: 1px solid black;text-align: center;'> Unit Of Measure </th>
                        </tr>
                    </thead>
                    <tbody>"""
        body = """</span>"""
        row = "even"
        for product in product_list:
            if row == "even":
                row = "odd"
                body = body + """<tr  style='background-color:#ffffff;line-height:25px'>
                                            <td style='text-align: center;border: 1px solid black;'>
                                            <span>"""
            else:
                row = "even"
                body = body + """<tr  style='background-color:#f0f8ff;line-height:25px'>
                                               <td style='text-align: center;border: 1px solid black;'>
                                               <span>"""
            body = body + str(product.get('product_name'))
            body = body + """</span>
                                        </td>
                                        <td style='text-align: center;border: 1px solid black;'>
                                        <span>"""
            body = body + str(product.get('sale_price'))
            body = body + """</span>
                                       </td>
                                       <td style='text-align: center;border: 1px solid black;'>
                                        <span>"""
            body = body + str(product.get('standard_price'))
            body = body + """
                                        </span>
                                        </td>
                                        <td style='text-align: center;border: 1px solid black;'>
                                        <span>"""
            body = body + str(product.get('product_type'))
            body = body + """</span>
                                        </td>
                                        <td style='text-align: center;border: 1px solid black;'>
                                        <span>"""
            body = body + str(product.get('minExDate'))
            body = body + """</span>
                                        </td>
                                        <td style='text-align: center;border: 1px solid black;'>
                                        <span>"""
            body = body + str(product.get('maxExDate'))
            body = body + """</span>
                                        </td>
                                        <td style='text-align: center;border: 1px solid black;'>
                                        <span>"""
            body = body + str(product.get('qty_on_hand'))
            body = body + """</span>
                                        </td>
                                        <td style='text-align: center;border: 1px solid black;'>
                                        <span>"""
            body = body + str(product.get('forecasted_qty'))
            body = body + """</span>
                                        </td>
                                         <td style='text-align: center;border: 1px solid black;'>
                                        <span>"""
            body = body + str(product.get('unit_of_measure'))
            body = body + """</span>
                                        </td>
                                        </tr>"""

        footer = """</tbody>
                                    </table>
                                    </div>
                                      <div >
                                      </div>
                                      <div  style="margin-top:20px">
                                        <p>Thanks & Regards,</p>
                                        <p> Admin Team </p>
                                      </div>
                                    </div>
                                </html>"""
        finalHTML=header+body+footer
        return finalHTML