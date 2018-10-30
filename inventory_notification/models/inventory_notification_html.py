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

    def process_common_html(self, subject, descrption, product_list, headers, columnProps):
        t_head=""
        header_description = """
        <html>
            <div style='margin:auto;width:100%;background-color: #ffffff; padding-left: 60px;' class='oe_structure'>
                <div >
                    <h2>""" + subject + """</h2>
                    <p>Hi Team,</p>
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