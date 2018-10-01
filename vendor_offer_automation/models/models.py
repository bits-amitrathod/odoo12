# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import datetime

import logging
import base64
import math

try:
    import xlrd

    try:
        from xlrd import xlsx
    except ImportError:
        xlsx = None
except ImportError:
    xlrd = xlsx = None

from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc

from odoo.exceptions import ValidationError, AccessError

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
                    else:
                        raise ValidationError(
                            _('Template Not found, Import Template For Vendor in Settings Menu'))
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
                            un_matched_rows = 0
                            if not sku_code in product_skus:
                                product_template = self.env['product.template'].search(
                                    ['|', ('sku_code', '=', product_sku), ('manufacturer_pref', '=', sku_code)])
                                if product_template:
                                    products = self.env['product.product'].search(
                                        [('product_tmpl_id', '=', product_template.id)])
                                    product_unit_price = product_template.list_price
                                    if len(products) > 0:
                                        order_line_obj = dict(name=product_template.name, product_qty=1,
                                                              date_planned=todays_date, state='ven_draft',
                                                              product_uom=1, product_tier=product_template.tier.id,
                                                              order_id=self.id,
                                                              product_id=products[0].id,
                                                              list_price=product_unit_price,
                                                              qty_in_stock=products[0].qty_available,
                                                              expiration_date=product_expiration_date)
                                        order_line_obj.update(self.get_product_sales_count(products[0].id))
                                        multiplier_id = self.get_order_line_multiplier(
                                            order_line_obj, product_template.premium)
                                        order_line_obj.update({'multiplier': multiplier_id})
                                        multiplier_list = self.env['multiplier.multiplier'].search(
                                            [('id', '=', multiplier_id)])
                                        possible_competition_list = self.env['competition.competition'].search(
                                            [('id', '=', self.possible_competition.id)])
                                        order_line_obj.update({'margin': multiplier_list.margin})
                                        product_unit_price_wtih_multiplier = math.ceil(
                                            round(float(product_unit_price) * (float(multiplier_list.retail) / 100), 2))
                                        order_line_obj.update({
                                            'price_unit' : product_unit_price_wtih_multiplier,
                                                'product_retail':product_unit_price_wtih_multiplier,
                                                'product_unit_price': product_unit_price_wtih_multiplier})
                                        product_offer_price_comp = math.ceil(
                                            round(float(product_unit_price_wtih_multiplier) * (
                                                    float(multiplier_list.margin) / 100 + float(
                                                possible_competition_list.margin) / 100), 2))
                                        order_line_obj.update(
                                            {'product_offer_price': product_offer_price_comp, 'offer_price': product_offer_price_comp})
                                        order_list_list.append(order_line_obj)
                                else:
                                    un_matched_rows = un_matched_rows + 1
                                product_skus.append(sku_code)
                        if len(order_list_list) > 0:
                            for order_line_object in order_list_list:
                                order_line_model = self.env['purchase.order.line'].with_context(order_line_object)
                                order_line_model.create(order_line_object)
                            # for purchase_order_line in self.order_line:
                            #     purchase_order_line.onchange_product_id_vendor_offer()


            except UnicodeDecodeError as ue:
                _logger.info(ue)

    def get_order_line_multiplier(self, order_line_obj, premium):
        multiplier_list = None
        if not order_line_obj['product_tier']:
            multiplier_list = self.env['multiplier.multiplier'].search([('code', '=', 'out of scope')])
        elif int(order_line_obj['product_sales_count']) == 0:
            multiplier_list = self.env['multiplier.multiplier'].search([('code', '=', 'no history')])
        elif float(order_line_obj['qty_in_stock']) > (float(order_line_obj['product_sales_count']) * 2) and \
                order_line_obj['product_sales_count'] != 0:
            multiplier_list = self.env['multiplier.multiplier'].search([('code', '=', 'overstocked')])
        elif premium is True:
            multiplier_list = self.env['multiplier.multiplier'].search([('code', '=', 'premium')])
        elif order_line_obj['product_tier'] == 1:
            multiplier_list = self.env['multiplier.multiplier'].search([('code', '=', 't1 good 45')])
        elif order_line_obj['product_tier'] == 2:
            multiplier_list = self.env['multiplier.multiplier'].search([('code', '=', 't2 good 35')])
        if multiplier_list is None:
            return False
        return multiplier_list.id

    # @api.multi
    # def qty_in_stocks(self, product_id):
    #     domain = [
    #         ('product_id', '=', product_id),
    #     ]
    #     moves = self.env['product.template'].search(domain, limit=1)
    #     mqty = moves.product_qty
    #     return mqty

    @api.multi
    def get_product_sales_count(self, product_id):
        product_sales_count = product_sales_count_month = product_sales_count_90 = product_sales_count_yrs = None
        try:
            groupby_dict = groupby_dict_month = groupby_dict_90 = groupby_dict_yr = {}
            sale_orders_line = self.env['sale.order.line'].search(
                [('product_id', '=', product_id), ('state', '=', 'sale')])
            groupby_dict['data'] = sale_orders_line
            total = total_m = total_90 = total_yr = 0

            for sale_order in groupby_dict['data']:
                total = total + sale_order.product_uom_qty

            product_sales_count = total
            sale_orders = self.env['sale.order'].search(
                [('product_id', '=', self.product_id.id), ('state', '=', 'sale')])

            filtered_by_date = list(
                filter(lambda x: fields.Datetime.from_string(x.confirmation_date).date() >= (
                        fields.date.today() - datetime.timedelta(days=30)), sale_orders))
            groupby_dict_month['data'] = filtered_by_date
            for sale_order_list in groupby_dict_month['data']:
                for sale_order in sale_order_list.order_line:
                    if sale_order.product_id.id == product_id:
                        total_m = total_m + sale_order.product_uom_qty

            product_sales_count_month = total_m

            filtered_by_90 = list(filter(lambda x: fields.Datetime.from_string(x.confirmation_date).date() >= (
                    fields.date.today() - datetime.timedelta(days=90)), sale_orders))
            groupby_dict_90['data'] = filtered_by_90

            for sale_order_list_90 in groupby_dict_90['data']:
                for sale_order in sale_order_list_90.order_line:
                    if sale_order.product_id.id == product_id:
                        total_90 = total_90 + sale_order.product_uom_qty

            product_sales_count_90 = total_90

            filtered_by_yr = list(filter(lambda x: fields.Datetime.from_string(x.confirmation_date).date() >= (
                    fields.date.today() - datetime.timedelta(days=365)), sale_orders))
            groupby_dict_yr['data'] = filtered_by_yr
            for sale_order_list_yr in groupby_dict_yr['data']:
                for sale_order in sale_order_list_yr.order_line:
                    if sale_order.product_id.id == product_id:
                        total_yr = total_yr + sale_order.product_uom_qty

            product_sales_count_yrs = total_yr
        except Exception as ex:
            _logger.error("Error", ex)
        return dict(product_sales_count=product_sales_count, product_sales_count_month=product_sales_count_month,
                    product_sales_count_90=product_sales_count_90, product_sales_count_yrs=product_sales_count_yrs)

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




class VendorOfferProductAuto(models.Model):
    _inherit = "purchase.order.line"

    def update_product_expiration_date(self):
        if self.order_id.document is None:
            for order in self:
                order.env.cr.execute(
                    "SELECT min(use_date), max(use_date) FROM public.stock_production_lot where product_id =" + str(
                        order.product_id.id))
                query_result = order.env.cr.dictfetchone()
                if query_result['max'] != None:
                    self.expiration_date = fields.Datetime.from_string(str(query_result['max'])).date()



