import re
from itertools import product

from .VendorOfferAutomationTemplate import *
from odoo import models, fields, api, _
import datetime
from odoo.exceptions import UserError, ValidationError
import logging

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

all_field_import = 'all_field_import'
new_appraisal = 'new_appraisal'

class VendorOfferNewAppraisalImport(models.Model):
    _description = "Vendor Offer Import"
    _inherit = "purchase.order"

    def expired_inventory_fetch(self, prod_id):
        for line in self:
            expired_lot_count = 0
            test_id_list = self.env['stock.lot'].search([('product_id', '=', prod_id)])
            for prod_lot in test_id_list:
                if prod_lot.use_date:
                    if fields.Datetime.from_string(prod_lot.use_date).date() < fields.date.today():
                        expired_lot_count = expired_lot_count + 1

            return expired_lot_count

    def get_inv_ratio_90_days(self, qty_in_stock, product_sales_count_90):
        return qty_in_stock / product_sales_count_90 if product_sales_count_90 != 0 else 0

    def get_consider_dropping_tier(self, qty_in_stock, product_sales_count_90, product_sales_count_yrs):
        if product_sales_count_90 != 0:
            condition = qty_in_stock / product_sales_count_90 > 4
        else:
            condition = False

        result = condition and product_sales_count_yrs >= qty_in_stock
        return result

    def get_quotations_count_by_product(self, prod_id):

        self.env.cr.execute("select "
                            "so.id, so.name "
                            "from sale_order so "
                            "right join sale_order_line sol "
                            "on so.id = sol.order_id and sol.product_id = " + str(prod_id) +
                            " where so.state in ('draft','send')")
        data = self.env.cr.dictfetchall()

        return len(data) if data else 0


    def action_import_order_lines_all_column(self):
        # tree_view_id = self.env.ref('vendor_offer_automation.vendor_template_client_action').id
        action = {
            'type': 'ir.actions.client',
            # 'views': [(tree_view_id, 'form')],
            'view_mode': 'form',
            'tag': 'import_offer_template',
            'params': {
                'model': 'sps.vendor_offer_automation.template',
                'request_model': 'sps.vendor_offer_automation.template',
                'offer_id': self.id,
                'vendor_id': self.partner_id.id,
                'user_type': 'supplier',
                'import_type_ven': all_field_import},
        }
        return action
    def action_import_order_lines_app_new(self):
        # tree_view_id = self.env.ref('vendor_offer_automation.vendor_template_client_action').id
        action = {
            'type': 'ir.actions.client',
            # 'views': [(tree_view_id, 'form')],
            'view_mode': 'form',
            'tag': 'import_offer_template',
            'params': {
                'model': 'sps.vendor_offer_automation.template',
                'request_model': 'sps.vendor_offer_automation.template',
                'offer_id': self.id,
                'vendor_id': self.partner_id.id,
                'user_type': 'supplier',
                'import_type_ven': 'new_appraisal'
            },
        }
        return action

    @staticmethod
    def _read_xls_book(book, pricing_index, flag, read_data=False, expiration_date_index=-1):
        sheet = book.sheet_by_index(pricing_index)
        data = []
        row_index = 0
        # for rowx, row in enumerate(map(sheet.row, range(sheet.nrows)), 1):
        for rowx, row in enumerate(map(sheet.row, range(sheet.nrows))):
            if read_data is True and row_index == 0:
                row_index = row_index + 1
                continue
            values = []
            cell_index = 0
            for cell in row:
                try:
                    if cell.ctype is xlrd.XL_CELL_NUMBER:
                        is_float = cell.value % 1 != 0.0
                        format = "%d" if (cell.value).is_integer() else "%s"
                        converted_val = format % cell.value
                        values.append(converted_val)
                    else:
                        values.append(cell.value)
                    cell_index = cell_index + 1
                except:
                    raise ValueError(_("Invalid value '%s'") % cell.value)
            data.append(values)
            if not read_data:
                break
            row_index = row_index + 1
        return data

    @api.model
    def map_customer_sku_with_catelog_number_app_new(self, vals):
        if self.document is not False:
            try:
                book = xlrd.open_workbook(file_contents=vals['document'])
                try:
                    pricing_index = book.sheet_names().index('PPVendorPricing')
                except:
                    pricing_index = 0
                excel_columns = VendorOfferNewAppraisalImport._read_xls_book(book, pricing_index, 1, read_data=False)
                if len(excel_columns) == 1:
                    excel_columns = excel_columns[0]
                    vendor_offer_automation_template_all_column = self.env[
                        'sps.vendor_offer_automation.template'].search(
                        [('id', '=', self.template_id.id)])
                    model_fields = self.env['sps.vendor_offer_automation.template'].fields_get()
                    mapping_fields = dict()
                    for name, field in model_fields.items():
                        if name.startswith('mf_'):
                            value = getattr(vendor_offer_automation_template_all_column, name, False)
                            if value:
                                mapping_fields.update({name: value})
                    sku_index = None
                    order_list_list = []
                    sku_not_found_list = []
                    sku_not_found_list_cleaned = []
                    expiration_date_index = uom_index = -1
                    quantity_index = False
                    price_index = False
                    credit_index = False

                    if 'mf_customer_sku' in mapping_fields:
                        sku_index = excel_columns.index(mapping_fields['mf_customer_sku'])
                    if 'mf_expiration_date' in mapping_fields:
                        expiration_date_index = excel_columns.index(mapping_fields['mf_expiration_date'])
                    if 'mf_uom_ven' in mapping_fields:
                        uom_index = excel_columns.index(mapping_fields['mf_uom_ven'])
                    if 'mf_quantity' in mapping_fields:
                        quantity_index = excel_columns.index(mapping_fields['mf_quantity'])

                    # if 'mf_price' in mapping_fields:
                    #     price_index = excel_columns.index(mapping_fields['mf_price'])
                    #
                    # if 'mf_possible_competition' in mapping_fields:
                    #     possible_competition_index = excel_columns.index(mapping_fields['mf_possible_competition'])
                    # if 'mf_multiplier' in mapping_fields:
                    #     multiplier_index = excel_columns.index(mapping_fields['mf_multiplier'])

                    if 'mf_credit' in mapping_fields:
                        credit_index = excel_columns.index(mapping_fields['mf_credit'])

                    if sku_index is not None:
                        today_date = datetime.datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                        excel_data_rows = VendorOfferNewAppraisalImport._read_xls_book(book, pricing_index, 1,
                                                                                       read_data=True,
                                                                                       expiration_date_index=
                                                                                       expiration_date_index)
                        count_obj = potential_profit_margin = max_val = 0
                        accelerator = credit = 'NO'
                        for excel_data_row in excel_data_rows:
                            sku_code = excel_data_row[sku_index]
                            original_sku = sku_code
                            price = sales_count = sales_count_yr = sales_total = sales_count_90 = 0
                            quantity = 1
                            sale_count_month = 0
                            quantity_in_stock = offer_price = offer_price_total = retail_price = retail_price_total = 0
                            possible_competition_name = multiplier_name = margin_cost = 0
                            expiration_date = False
                            uom = ''

                            # if price_index and price_index >= 0:
                            #     price = excel_data_row[price_index]

                            if quantity_index and quantity_index >= 0:
                                quantity = excel_data_row[quantity_index]

                            if count_obj == 0:
                                if credit_index and credit_index >= 0:
                                    credit = excel_data_row[credit_index]

                            if expiration_date_index and expiration_date_index >= 0:
                                expiration_date = excel_data_row[expiration_date_index]
                            if uom_index and uom_index >= 0:
                                uom = excel_data_row[uom_index]

                            product_sku = sku_code
                            if self.partner_id.sku_preconfig and product_sku.startswith(
                                    self.partner_id.sku_preconfig):
                                product_sku = product_sku[len(self.partner_id.sku_preconfig):]
                            if self.partner_id.sku_postconfig and product_sku.endswith(
                                    self.partner_id.sku_postconfig):
                                product_sku = product_sku[:-len(self.partner_id.sku_postconfig)]

                            self.env.cr.execute("""
                                                    select * from 
                                                        (SELECT pp.id as product_id,pt.id as id,pt.list_price as 
                                                        list_price,pt.uom_id as uom_id, pt.name as name, pt.premium as
                                                        premium, pt.tier as tier, 
                                                         UPPER(regexp_replace(manufacturer_pref , '[^A-Za-z0-9.]', '','g')) 
                                                         as manufacturer_pref, 
                                                          UPPER(regexp_replace(sku_code , '[^A-Za-z0-9.]', '','g'))
                                                           as sku_code_cleaned 
                                                          FROM product_template as pt join product_product as pp on 
                                                           pt.id=pp.product_tmpl_id where pt.active=true) 
                                                    as temp_data where sku_code_cleaned ='""" + re.sub(
                                r'[^A-Za-z0-9.]', '', product_sku.upper()) + """' or manufacturer_pref = '""" + re.sub(
                                r'[^A-Za-z0-9.]', '', sku_code.upper()) + """' """)

                            query_result = self.env.cr.dictfetchall()

                            if len(query_result) == 0 and product_sku.startswith("M00"):
                                prod_sku = product_sku[4:]
                                final_sku = prod_sku[:len(prod_sku)-1]
                                self.env.cr.execute("""
                                                    select * from 
                                                        (SELECT pp.id as product_id,pt.id as id,pt.list_price as 
                                                        list_price,pt.uom_id as uom_id, pt.name as name, pt.premium as
                                                        premium, pt.tier as tier, 
                                                         UPPER(regexp_replace(manufacturer_pref , '[^A-Za-z0-9.]', '','g')) 
                                                         as manufacturer_pref, 
                                                          UPPER(regexp_replace(sku_code , '[^A-Za-z0-9.]', '','g'))
                                                           as sku_code_cleaned 
                                                          FROM product_template as pt join product_product as pp on 
                                                           pt.id=pp.product_tmpl_id where pt.active=true) 
                                                    as temp_data where sku_code_cleaned ='""" + re.sub(
                                    r'[^A-Za-z0-9.]', '', final_sku.upper()) + """' or manufacturer_pref ='""" + re.sub(
                                    r'[^A-Za-z0-9.]', '', sku_code.upper()) + """' """)
                                #query_result = self.env.cr.dictfetchone()
                                query_result = self.env.cr.dictfetchall()

                            sku_code_file = re.sub('[^A-Za-z0-9]+', '', product_sku)
                            if query_result:
                                for query_result_one in query_result:
                                    products = self.env['product.product'].browse(query_result_one['product_id'])
                                    # if count_obj == 0:
                                    #     possible_competition = self.env['competition.competition'].search(
                                    #         [('name', '=', possible_competition_name)]).id
                                    # multiplier = self.env['multiplier.multiplier'].search(
                                    #     [('name', '=', multiplier_name)]).id
                                    prod_id = 0
                                    prod_name = ''
                                    if products:
                                        prod_id = products[0].id
                                        prod_name = products[0].name
                                    flag_red = False
                                    if len(query_result) > 1:
                                        flag_red = True
                                    list_contains_equip = False
                                    if products.categ_id and products.categ_id.name == 'EQUIPMENT':
                                        list_contains_equip = True
                                        flag_red = False

                                    if prod_id != 0:
                                        order_line_obj = dict(name=product_sku, product_qty=quantity,
                                                              product_qty_app_new=quantity,
                                                              date_planned=today_date,
                                                              state='ven_draft',
                                                              prod_name=prod_name,
                                                              product_uom=query_result_one['uom_id'],
                                                              order_id=self.id,
                                                              product_id=prod_id,
                                                              qty_in_stock=products[0].qty_available,
                                                              price_unit=offer_price,
                                                              product_retail=0,
                                                              product_unit_price=0, product_offer_price=0,
                                                              product_sales_count_90=sales_count_90,
                                                              product_sales_count_yrs=sales_count_yr,
                                                              product_sales_count=sales_count,
                                                              amount_total_ven_pri=sales_total,
                                                              expired_inventory=0,
                                                              offer_price=offer_price, offer_price_total=offer_price_total,
                                                              retail_price=retail_price,
                                                              retail_price_total=retail_price_total,
                                                              possible_competition=None,
                                                              multiplier=None,
                                                              potential_profit_margin=potential_profit_margin,
                                                              max_val=max_val, accelerator=accelerator, credit=credit,
                                                              margin=margin_cost,
                                                              import_type_ven_line=new_appraisal,
                                                              product_multiple_matches=flag_red,
                                                              list_contains_equip=list_contains_equip,
                                                              original_sku=original_sku,
                                                              product_sales_count_month=sale_count_month,
                                                              product_sales_amount_yr=0,
                                                              open_quotations_of_prod=0,
                                                              inv_ratio_90_days=0,
                                                              consider_dropping_tier=False

                                                              )
                                        if expiration_date:
                                            order_line_obj.update({'expiration_date': expiration_date})
                                        else:
                                            order_line_obj.update({'expiration_date': None})
                                        if uom:
                                            if uom.upper() == 'EACH':
                                                order_line_obj.update({'uom_str': uom})
                                            if uom.upper() == 'BOX':
                                                uom_obj = products[0].manufacturer_uom
                                                temp_qty = uom_obj.factor_inv * float(quantity)
                                                order_line_obj.update({'uom_str': 'each'})
                                                order_line_obj.update({'product_qty': temp_qty})
                                                order_line_obj.update({'product_qty_app_new': temp_qty})
                                        else:
                                            order_line_obj.update({'uom_str': ''})
                                        order_list_list.append(order_line_obj)
                                        count_obj = count_obj + 1
                                    else:
                                        sku_not_found_list.append(sku_code)
                                        sku_not_found_list_cleaned.append(sku_code_file)
                            else:
                                sku_not_found_list.append(sku_code)
                                sku_not_found_list_cleaned.append(sku_code_file)

                        # if len(sku_not_found_list) > 0:
                        #     raise ValueError(_("Following SKU does not match \n\n\n %s") % sku_not_found_list)

                        count_order = 0
                        if len(order_list_list) > 0:
                            amount_untaxed = amount_total = 0

                            for order_line_object_add in order_list_list:
                                try:
                                    float(order_line_object_add['product_qty'])
                                except:
                                    raise ValueError(_("Quantity contains incorrect values '%s' ")
                                                     % order_line_object_add['product_qty'])

                                amount_untaxed = amount_untaxed + float(order_line_object_add['offer_price_total'])
                                amount_total = amount_total + float(order_line_object_add['offer_price_total'])

                            currency_id_insert = create_uid = company_id = create_date = 0
                            for order_line_object in order_list_list:
                                exp_date = exp_date_str = None
                                try:
                                    today_date = datetime.datetime.now()
                                    last_3_months = fields.Date.to_string(today_date - datetime.timedelta(days=90))
                                    last_month = fields.Date.to_string(today_date - datetime.timedelta(days=30))
                                    last_yr = fields.Date.to_string(today_date - datetime.timedelta(days=365))
                                    str_query_cm_new = """
                                                        select sum(sol.qty_delivered),sum(sol.price_subtotal) as amt 
                                                        from sale_order AS so JOIN 
                                                        sale_order_line AS sol ON  so.id = sol.order_id where 
                                                        sol.product_id = %s and sol.state in ('sale','done')
                                                        and sol.qty_delivered > 0
                                                       """
                                    self.env.cr.execute(str_query_cm_new + " AND so.date_order>=%s",
                                                        (order_line_object['product_id'], last_3_months))
                                    quant_90 = self.env.cr.fetchone()
                                    if quant_90[0] is not None:
                                        order_line_object['product_sales_count_90'] = int(quant_90[0])

                                    self.env.cr.execute(str_query_cm_new + " AND so.date_order>=%s",
                                                        (order_line_object['product_id'], last_month))
                                    quant_m = self.env.cr.fetchone()
                                    if quant_m[0] is not None:
                                        order_line_object['product_sales_count_month'] = int(quant_m[0])

                                    self.env.cr.execute(str_query_cm_new + " AND so.date_order>=%s",
                                                        (order_line_object['product_id'], last_yr))
                                    quant_yr = self.env.cr.fetchone()
                                    if quant_yr[0] is not None:
                                        order_line_object['product_sales_count_yrs'] = int(quant_yr[0])

                                    self.env.cr.execute(str_query_cm_new, [order_line_object['product_id']])
                                    quant_all = self.env.cr.fetchone()
                                    if quant_all[0] is not None:
                                        order_line_object['product_sales_count'] = int(quant_all[0])

                                    self.env.cr.execute(str_query_cm_new + " AND so.date_order>=%s",
                                                        (order_line_object['product_id'], last_yr))
                                    quant_yr = self.env.cr.fetchone()
                                    if quant_yr[1] is not None:
                                        order_line_object['product_sales_amount_yr'] = quant_yr[1]

                                    order_line_object['open_quotations_of_prod'] = \
                                        self.get_quotations_count_by_product(order_line_object['product_id'])
                                    order_line_object['inv_ratio_90_days'] = \
                                        self.get_inv_ratio_90_days(order_line_object['qty_in_stock'],
                                                                   order_line_object['product_sales_count_90'])
                                    order_line_object['expired_inventory'] = \
                                        self.expired_inventory_fetch(order_line_object['product_id'])
                                    order_line_object['consider_dropping_tier'] = \
                                        self.get_consider_dropping_tier(order_line_object['qty_in_stock'],
                                                                        order_line_object['product_sales_count_90'],
                                                                        order_line_object['product_sales_count_yrs'])

                                    temp_date = float(order_line_object['expiration_date'])

                                    def floatHourToTime(fh):
                                        h, r = divmod(fh, 1)
                                        m, r = divmod(r * 60, 1)
                                        return (
                                            int(h),
                                            int(m),
                                            int(r * 60),
                                        )

                                    dt = datetime.datetime.fromordinal(
                                        datetime.datetime(1900, 1, 1).toordinal() + int(temp_date) - 2)
                                    hour, minute, second = floatHourToTime(temp_date % 1)
                                    dt = dt.replace(hour=hour, minute=minute, second=second)
                                    exp_date_str = datetime.datetime.strftime(dt, '%m/%d/%Y')
                                except:
                                    exp_date_str = order_line_object['expiration_date']
                                if count_order == 0:
                                    order_model = self.env['purchase.order'].search([('id', '=',
                                                                                      order_line_object['order_id'])])
                                    temp_acc = False
                                    if (order_line_object['accelerator']).upper() == 'YES':
                                        temp_acc = True
                                    temp_offer_type = 'cash'
                                    if (order_line_object['credit']).upper() == 'YES':
                                        temp_offer_type = 'credit'
                                    order_model.write({'accelerator': temp_acc})
                                    order_model.write({'offer_type': temp_offer_type})
                                    order_model.write({'amount_untaxed': amount_untaxed})
                                    order_model.write({'amount_total': amount_total})
                                    order_model.write({'possible_competition': None})
                                    order_model.write({'date_planned': order_line_object['date_planned']})
                                    order_model.write({'no_match_sku_import': sku_not_found_list})
                                    order_model.write({'no_match_sku_import_cleaned': sku_not_found_list_cleaned})
                                    currency_id_insert = order_model.currency_id.id
                                    create_uid = order_model.create_uid.id
                                    company_id = order_model.company_id.id
                                    create_date = order_model.create_date
                                    count_order = count_order + 1

                                insert = "INSERT INTO purchase_order_line" \
                                         "(name,product_uom,price_unit,product_qty,product_qty_app_new," \
                                         "date_planned,order_id," \
                                         "product_id," \
                                         " qty_in_stock," \
                                         "product_unit_price,product_offer_price,product_sales_count_90" \
                                         " , product_sales_count_yrs,product_sales_count,expired_inventory," \
                                         " price_total," \
                                         " multiplier," \
                                         "expiration_date,uom_str,expiration_date_str," \
                                         " import_type_ven_line,currency_id,product_sales_count_month" \
                                         " ,create_uid,company_id,create_date,price_tax,qty_invoiced" \
                                         ",qty_to_invoice,propagate_cancel,qty_received_method,product_uom_qty," \
                                         " qty_received,state,product_multiple_matches,list_contains_equip," \
                                         " original_sku,product_sales_amount_yr," \
                                         " open_quotations_of_prod,inv_ratio_90_days" \
                                         ",consider_dropping_tier)" \
                                         " VALUES (%s,%s,%s, %s,%s, %s, %s,%s," \
                                         " %s, " \
                                         " %s, %s, %s," \
                                         " %s, " \
                                         " %s,%s, %s, " \
                                         " %s," \
                                         " %s, %s , %s ," \
                                         " %s ,%s,%s ," \
                                         " %s ,%s,%s ,%s,%s," \
                                         " %s,%s,%s,%s," \
                                         " %s,%s,%s,%s," \
                                         " %s,%s," \
                                         "  %s,%s," \
                                         " %s ) " \
                                         " RETURNING id"

                                sql_query = insert
                                val = (order_line_object['prod_name'], order_line_object['product_uom'],
                                       float("{0:.2f}".format(float(order_line_object['offer_price']))),
                                       int(order_line_object['product_qty']),  order_line_object['product_qty_app_new'],
                                       order_line_object['date_planned'],
                                       order_line_object['order_id'], order_line_object['product_id'],
                                       order_line_object['qty_in_stock'],
                                       float("{0:.2f}".format(float(order_line_object['retail_price']))),
                                       float("{0:.2f}".format(float(order_line_object['offer_price']))),
                                       order_line_object['product_sales_count_90'],
                                       order_line_object['product_sales_count_yrs'],
                                       order_line_object['product_sales_count'],
                                       order_line_object['expired_inventory'],
                                       float("{0:.2f}".format(float(order_line_object['offer_price_total']))),
                                       None,
                                       exp_date, order_line_object['uom_str'], exp_date_str,
                                       order_line_object['import_type_ven_line'],
                                       currency_id_insert, order_line_object['product_sales_count_month'],
                                       create_uid, company_id, create_date, 0, 0, 0, 'true',
                                       'stock_moves',
                                       order_line_object['product_qty'], 0, 'ven_draft',
                                       order_line_object['product_multiple_matches'],
                                       order_line_object['list_contains_equip'],
                                       order_line_object['original_sku'],
                                       order_line_object['product_sales_amount_yr'],
                                       order_line_object['open_quotations_of_prod'],
                                       order_line_object['inv_ratio_90_days'],
                                       order_line_object['consider_dropping_tier'])

                                self._cr.execute(sql_query, val)
                                line_obj = self._cr.fetchone()
                                line_order_model = self.env['purchase.order.line'].search(
                                    [('id', 'in', line_obj)])
                                line_order_model.price_subtotal = float(order_line_object['offer_price_total'])

            except UnicodeDecodeError as ue:
                _logger.info(ue)


