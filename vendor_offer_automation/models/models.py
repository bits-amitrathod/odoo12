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
                _logger.info("books %r", book.sheet_names())
                excel_data_rows_with_columns = vendor_offer_automation._read_xls_book(book, pricing_index, read_data=True)
                if len(excel_data_rows_with_columns) > 1:
                    excel_data_rows = [excel_data_rows_with_columns[idx] for idx in
                                       range(1, len(excel_data_rows_with_columns) - 1)]
                    excel_columns = excel_data_rows_with_columns[0]
                    vendor_offer_automation_template = self.env['sps.vendor_offer_automation.template'].search(
                        [('customer_id', '=', self.partner_id.id), ('template_status', '=', 'Active')])
                    if len(vendor_offer_automation_template) > 0:
                        sorted_excel_columns = ','.join(sorted(excel_columns))
                        if vendor_offer_automation_template.columns_from_template != sorted_excel_columns:
                            raise ValidationError(
                                _('Document columns are not matching active offer template ' + self.template_name))
                    _logger.info(excel_columns)
                    model_fields = self.env['sps.vendor_offer_automation.template'].fields_get()
                    mapping_fields = dict()
                    for name, field in model_fields.items():
                        if name.startswith('mf_'):
                            value = getattr(vendor_offer_automation_template, name, False)
                            if value:
                                mapping_fields.update({name: value})
                    sku_index = None
                    order_list_list = []
                    if 'mf_customer_sku' in mapping_fields:
                        sku_index = excel_columns.index(mapping_fields['mf_customer_sku'])
                    if not sku_index is None:
                        todays_date = datetime.datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                        for excel_data_row in excel_data_rows:
                            sku_code = excel_data_row[sku_index]
                            product_template = self.env['product.template'].search([('sku_code', '=', sku_code)])
                            if product_template:
                                products = self.env['product.product'].search(
                                    [('product_tmpl_id', '=', product_template.id)])
                                if len(products) > 0:
                                    order_list_list.append(
                                        dict(name=product_template.name, product_qty=1, date_planned=todays_date,
                                             product_uom=1,
                                             order_id=self.id,
                                             product_id=products.id, price_unit=product_template.list_price,
                                             product_unit_price=product_template.list_price))
                        for order_line_object in order_list_list:
                            order_line_model = self.env['purchase.order.line'].with_context(order_line_object)
                            order_line_model.create(order_line_object)
                            # _logger.info('products_list %r', order_line_object)
            except UnicodeDecodeError as ue:
                _logger.info(ue)

    @staticmethod
    def _read_xls_book(book, pricing_index, read_data=False):
        sheet = book.sheet_by_index(pricing_index)
        data = []
        for row in pycompat.imap(sheet.row, range(sheet.nrows)):
            values = []
            for cell in row:
                if cell.ctype is xlrd.XL_CELL_NUMBER:
                    is_float = cell.value % 1 != 0.0
                    values.append(
                        pycompat.text_type(cell.value)
                        if is_float
                        else pycompat.text_type(int(cell.value))
                    )
                else:
                    values.append(cell.value)
            data.append(values)
            if not read_data:
                break
        return data

    @staticmethod
    def _get_unit_price(default_code, ven_product_prices_list):
        unit_price = None
        descptn = None
        for ven_product_price in ven_product_prices_list:
            if ven_product_price['sku_code'] == default_code:
                unit_price = ven_product_price['unit_price']
                descptn = ven_product_price['description']
                break
        return unit_price, descptn

    @api.multi
    def write(self, vals):
        res = super(vendor_offer_automation, self).write(vals)
        return res

    def update_template_name(self):
        for order in self:
            vendor_offer_templates = order.env['sps.vendor_offer_automation.template'].search(
                [('customer_id', '=', order.partner_id.id), ('template_status', '=', 'Active')])
            if len(vendor_offer_templates) > 0:
                order.template_name = vendor_offer_templates[0].file_name
                order.template_exists = True
                _logger.info('order.template_name %r %r', order.partner_id.id, order.template_name)
            else:
                order.template_exists = False

