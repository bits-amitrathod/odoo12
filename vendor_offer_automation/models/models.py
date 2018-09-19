# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import datetime

import logging
import base64
from odoo.exceptions import ValidationError

try:
    import xlrd

    try:
        from xlrd import xlsx
    except ImportError:
        xlsx = None
except ImportError:
    xlrd = xlsx = None

from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc

_logger = logging.getLogger(__name__)


class vendor_offer_automation(models.Model):
    _description = "Vendor Offer Automation"
    _inherit = "purchase.order"

    template_name = fields.Char(compute="_value_pc", store=True, reqiured=True)
    document = fields.Binary()
    filename = fields.Char(string='File')
    template_exists = fields.Boolean(default=False)

    @api.multi
    @api.depends('partner_id')
    def _value_pc(self):
       self.update_template_name()

    @api.multi
    @api.onchange('partner_id')
    def on_partner_changed(self):
        self.update_template_name()

    @api.model
    def create(self, vals):
        record = super(vendor_offer_automation, self).create(vals)
        record.map_customer_sku_with_catelog_number()
        return record

    @api.model
    def map_customer_sku_with_catelog_number(self):
        if not self.document is None:
            try:
                book = xlrd.open_workbook(file_contents=base64.b64decode(self.document))
                try:
                    pricing_index = book.sheet_names().index('PPVendorPricing')
                except:
                    pricing_index = 0
                excel_columns = vendor_offer_automation._read_xls_book(book, pricing_index, read_data=False)
                if len(excel_columns) == 1:
                    excel_columns = excel_columns[0]
                    vendor_offer_automation_template = self.env['sps.vendor_offer_automation.template'].search(
                        [('customer_id', '=', self.partner_id.id), ('template_status', '=', 'Active')])
                    if len(vendor_offer_automation_template) > 0:
                        sorted_excel_columns = ','.join(sorted(excel_columns))
                        if vendor_offer_automation_template.columns_from_template != sorted_excel_columns:
                            raise ValidationError(
                                _('Document columns are not matching active offer template ' + self.template_name))
                    model_fields = self.env['sps.vendor_offer_automation.template'].fields_get()
                    mapping_fields = dict()
                    for name, field in model_fields.items():
                        if name.startswith('mf_'):
                            value = getattr(vendor_offer_automation_template, name, False)
                            if value:
                                mapping_fields.update({name: value})
                    sku_index = None
                    order_list_list = []
                    expiration_date_index = -1
                    if 'mf_customer_sku' in mapping_fields:
                        sku_index = excel_columns.index(mapping_fields['mf_customer_sku'])
                    if 'mf_expiration_date' in mapping_fields:
                        expiration_date_index = excel_columns.index(mapping_fields['mf_expiration_date'])

                    if not sku_index is None:
                        todays_date = datetime.datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                        product_skus = []
                        excel_data_rows = vendor_offer_automation._read_xls_book(book, pricing_index, read_data=True,
                                                                                 expiration_date_index=expiration_date_index)
                        for excel_data_row in excel_data_rows:
                            sku_code = excel_data_row[sku_index]
                            product_expiration_date = excel_data_row[expiration_date_index]
                            product_sku = sku_code
                            if self.partner_id.sku_preconfig and product_sku.startswith(
                                    self.partner_id.sku_preconfig):
                                product_sku = product_sku[len(self.partner_id.sku_preconfig):]
                            if self.partner_id.sku_postconfig and product_sku.endswith(
                                    self.partner_id.sku_postconfig):
                                product_sku = product_sku[:-len(self.partner_id.sku_postconfig)]
                            if not sku_code in product_skus:
                                product_template = self.env['product.template'].search(
                                    ['|', ('sku_code', '=', product_sku), ('manufacturer_pref', '=', sku_code)])
                                if product_template:
                                    products = self.env['product.product'].search(
                                        [('product_tmpl_id', '=', product_template.id)])
                                    product_unit_price = product_template.list_price
                                    if len(products) > 0:
                                        order_list_list.append(
                                            dict(name=product_template.name, product_qty=1, date_planned=todays_date,
                                                 product_uom=1, product_tier=product_template.tier.id,
                                                 order_id=self.id, product_unit_price=product_unit_price,
                                                 product_id=products[0].id, price_unit=product_template.list_price,
                                                 expiration_date=product_expiration_date
                                                 ))
                                product_skus.append(sku_code)
                        if len(order_list_list) > 0:
                            for order_line_object in order_list_list:
                                order_line_model = self.env['purchase.order.line'].with_context(order_line_object)
                                order_line_model.create(order_line_object)
                            for purchase_order_line in self.order_line:
                                purchase_order_line.onchange_product_id_vendor_offer()

            except UnicodeDecodeError as ue:
                _logger.info(ue)

    @staticmethod
    def _read_xls_book(book, pricing_index, read_data=False, expiration_date_index=-1):
        sheet = book.sheet_by_index(pricing_index)
        data = []
        row_index = 0
        for row in pycompat.imap(sheet.row, range(sheet.nrows)):
            if read_data is True and row_index == 0:
                row_index = row_index + 1
                continue
            values = []
            cell_index = 0
            for cell in row:
                if expiration_date_index == cell_index and not cell.value is None and str(cell.value) != '':
                    is_datetime = cell.value % 1 != 0.0
                    # emulate xldate_as_datetime for pre-0.9.3
                    dt = datetime.datetime(*xlrd.xldate.xldate_as_tuple(cell.value, book.datemode))
                    values.append(
                        dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                        if is_datetime
                        else dt.strftime(DEFAULT_SERVER_DATE_FORMAT)
                    )
                else:
                    if cell.ctype is xlrd.XL_CELL_NUMBER:
                        is_float = cell.value % 1 != 0.0
                        values.append(
                            pycompat.text_type(cell.value)
                            if is_float
                            else pycompat.text_type(int(cell.value))
                        )
                    else:
                        values.append(cell.value)
                cell_index = cell_index + 1
            data.append(values)
            if not read_data:
                break
            row_index = row_index + 1
        return data

    @api.multi
    def write(self, vals):
        res = super(vendor_offer_automation, self).write(vals)
        if 'document' in vals:
            self.env["purchase.order.line"].search([('order_id', '=', self.id)]).unlink()
            self.map_customer_sku_with_catelog_number()
        return res

    def update_template_name(self):
        for order in self:
            vendor_offer_templates = order.env['sps.vendor_offer_automation.template'].search(
                [('customer_id', '=', order.partner_id.id), ('template_status', '=', 'Active')])
            if len(vendor_offer_templates) > 0:
                order.template_name = vendor_offer_templates[0].file_name
                order.template_exists = True
            else:
                order.template_exists = False

