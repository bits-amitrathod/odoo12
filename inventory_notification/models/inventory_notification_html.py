from odoo import models, fields, api,SUPERUSER_ID
import logging
import datetime
from datetime import date
import calendar
from odoo.exceptions import UserError
from odoo.tools import float_compare

_logger = logging.getLogger(__name__)


class InventoryNotificationHTML(models.TransientModel):
    _name = 'inventory.notification.html'
    def process_packing_list_html(self,packing_list):
        html_description="""
            <html>
            <div style='margin:auto;width:100%;background-color: #ffffff; padding-left: 60px;' class='oe_structure'/>
            <div>
                <div >
                    <p>Hi Team,</p>
                    <p>Please find below Packing list:  </p>
                </div>
    
                <center>
                </center>
            </div>"""

        body = ""
        for packing in packing_list:
            body=body+"""
            <div style="border: 1px solid #aaa; margin-top: 50px;background-color: #ffffff;">
                <div style="margin-left:10px;">
                    <p><span style="font-weight: bold;">Order Number:</span><span>""" +packing.sale_id.name + """</span></p>
                     <p><span style="font-weight: bold;">Dated On:</span>""" +str(packing.sale_id.write_date) + """</p>
                    <p><span style="font-weight: bold;">Customer Name:</span>""" +packing.sale_id.partner_id.display_name+ """</p>
                    <p>
                        <span style="font-weight: bold;">Shipping Address:</span>
                        <span> """ + self.check_isAvailable_product_code(packing.sale_id.partner_shipping_id.street) + """</span>
                        <span> """ +self.check_isAvailable_product_code(packing.sale_id.partner_shipping_id.street2) + """</span>
                        <span>""" +self.check_isAvailable_product_code(packing.sale_id.partner_shipping_id.city)+"""</span>
                        <span>""" +self.check_isAvailable_product_code(packing.sale_id.partner_shipping_id.state_id.name)+"""</span>
                        <span>"""+ self.check_isAvailable_product_code(packing.sale_id.partner_shipping_id.zip) + """"</span>
                        <span>""" + self.check_isAvailable_product_code(packing.sale_id.partner_shipping_id.country_id.name) + """</span>
                    </p>"""
            if packing.sale_id.client_order_ref != False:
                   body=body+ """<p><span style="font-weight: bold;">Customer PO Number:</span>""" + packing.sale_id.client_order_ref +"""</p>"""

            if packing.sale_id.carrier_info !=False:
                    body= body+"""<p><span style="font-weight: bold;">Carrier Name:</span>""" +packing.sale_id.carrier_info + """</p>"""

            if packing.sale_id.carrier_acc_no !=False:
                     body=body + """<p><span style="font-weight: bold;">Carrier Account Number:</span>""" + packing.sale_id.carrier_acc_no + """</p>"""

            if packing.sale_id.carrier_id.name !=False:
                     body=body + """<p><span style="font-weight: bold;">Delivery Method:</span>""" + packing.sale_id.carrier_id.name + """</p>"""

            body=body + """</div>
                            <br/>
                            <table style='border: 1px solid black;width:100%;margin-top:20px'>
                                <thead style='background-color:#D6DBDF;line-height: 30px'>
                                    <tr style='border: 1px solid black;'>
                                         <th style='border: 1px solid black;text-align: center; width: 100px;'>SKU Code</th>
                                         <th style='border: 1px solid black;text-align: center; width: 100px;'>Product Name</th>
                                         <th style='border: 1px solid black;text-align: center; width: 100px;'>Unit of Measure</th>
                                         <th style='border: 1px solid black;text-align: center; width: 100px;'>Lot#</th>
                                         <th style='border: 1px solid black;text-align: center; width: 100px;'>Ordered Qty</th>
                                    </tr>
                                </thead>
                            <tbody> """
            row_color = "#f0f8ff"
            for move_line in packing.move_lines:
                if row_color == "#f0f8ff":
                    row_color="#ffffff"
                    body=body+"""<tr  style='border: 1px solid black;line-height:25px;background-color:#ffffff'>"""
                else:
                    row_color="#f0f8ff"
                    body=body + """<tr  style='border: 1px solid black;line-height:25px;background-color:#f0f8ff'>  """
                body=body+ """<th style = 'text-align: center;border: 1px solid black;'>""" + self.check_isAvailable_product_code(move_line.product_tmpl_id.sku_code) + """</th>
                                <th style = 'text-align: center;border: 1px solid black;'>""" +move_line.product_tmpl_id.name+"""</th>
                                <th style = 'text-align: center;border: 1px solid black;'>"""+self.check_isAvailable_product_code(move_line.product_uom.name) + """</th>
                                <th style = 'text-align: center;border: 1px solid black;'>
                                <div style="margin-top:10px">"""
                for move_line_id in move_line.move_line_ids:
                    body=body+"""<p style="font-weight: lighter">
                        <span>"""+ str(move_line_id.qty_done) + """</span>
                        <span> """+ self.check_isAvailable_product_code(move_line.product_uom.name) + """</span>-"""

                    if  move_line_id.lot_id :
                           body=body+ """Lot#:<span>""" + move_line_id.lot_id.name+"""</span> Exp Date:<span>""" +  self.check_isAvailable_product_code(move_line_id.lot_id.use_date) + """</span>"""

                body=body+ """</p> </div>
                                  </th>
                                   <th style = 'text-align: center;border: 1px solid black;'>
                                        <div  style="margin-top:10px">
                                            <p style="font-weight: lighter">
                                                <span>""" + str(move_line.ordered_qty) +"""</span>
                                                <span>""" + self.check_isAvailable_product_code(move_line.product_uom.name)+  """</span>
                                            </p>
                                        </div>
                                    </th>
                                </tr>"""
                body=body+"""</tbody>
                        </table>
                    </div>"""
        body=body+"""<div  style="margin-top:20px">
                            <p>Thanks & Regards,</p>
                            <p> Admin Team </p>
                      </div>
                 </div>
              </html>   
        """
        final_html=html_description + body
        return final_html

    def process_common_html(self, subject, descrption, product_list, headers, columnProps):
        t_head=""
        header_description = """
        <html>
            <div style='margin:auto;width:100%;background-color: #ffffff; padding-left: 60px;' class='oe_structure'>
                <div >
                    <h2>""" + subject + """</h2>
                    <p>Hello ,</p>
                    """ + descrption + """ 
                </div>
                <div class='row'>  
            </div>
            <div>
                <table style='border: 1px solid black;width:100%;margin-top:20px'>
                 <thead style='background-color:#D6DBDF;line-height: 30px'>
                     <tr style='border: 1px solid black;'> """
        for headerName in headers:
            if headerName=='Serial Number':
                t_head = t_head + """ <th  style='border: 1px solid black;text-align: center; width: 100px;'>""" + headerName + """</th> """
            else:
                t_head= t_head + """ <th  style='border: 1px solid black;text-align: center;'>""" + headerName + """</th> """

        t_head=t_head+"""</tr>
                       </thead>
                       <tbody>"""
        body = """</span>"""
        row = "even"
        for product in product_list:
            if row == "even":
                row = "odd"
                body = body + """<tr  style='background-color:#ffffff;line-height:25px'>"""
            else:
                row = "even"
                body = body + """<tr  style='background-color:#f0f8ff;line-height:25px'>"""
            for column_name in columnProps:
                body = body + """<td style = 'text-align: center;border: 1px solid black;'><span>"""
                column=str(product.get(column_name))
                if column:
                    body = body + column
                body = body +"""</span></td>"""
            body= body+"""</tr>"""

        footer = """
                        </tbody>
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
        finalHTML = header_description+ t_head + body + footer
        return finalHTML

    def process_in_stock_html(self, subject, descrption, product_list, headers, columnProps):
        t_head=""
        header_description = """
        <html>
            <div style='margin:auto;width:100%;background-color: #ffffff; padding-left: 60px;' class='oe_structure'>
                <div >
                    <h2>""" + subject + """</h2>
                    <p>Hello ,</p>
                    """ + descrption + """ 
                </div>
                <div class='row'>  
            </div>
            <div>
                <table style='border: 1px solid black;width:100%;margin-top:20px'>
                 <thead style='background-color:#D6DBDF;line-height: 30px'>
                     <tr style='border: 1px solid black;'> """
        for headerName in headers:
            if headerName=='Serial Number':
                t_head = t_head + """ <th  style='border: 1px solid black;text-align: center; width: 100px;'>""" + headerName + """</th> """
            else:
                t_head= t_head + """ <th  style='border: 1px solid black;text-align: center;'>""" + headerName + """</th> """

        t_head=t_head+"""</tr>
                       </thead>
                       <tbody>"""
        body = """</span>"""
        row = "even"
        for product in product_list:
            if row == "even":
                row = "odd"
                body = body + """<tr  style='background-color:#ffffff;line-height:25px'>"""
            else:
                row = "even"
                body = body + """<tr  style='background-color:#f0f8ff;line-height:25px'>"""
            for column_name in columnProps:
                body = body + """<td style = 'text-align: center;border: 1px solid black;'><span>"""
                column=str(product.get(column_name))
                if column:
                    if column_name=='list_price':
                        body = body +"$ "+ column
                    else:
                        body = body + column
                body = body +"""</span></td>"""
            body= body+"""</tr>"""

        footer = """
                        </tbody>
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
        finalHTML = header_description+ t_head + body + footer
        return finalHTML

    def check_isAvailable_product_code(self, value):
        if value:
            return  str(value)
        return ""