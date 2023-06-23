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

    def action_import_order_lines_app_new(self):
        tree_view_id = self.env.ref('vendor_offer_automation.vendor_template_client_action').id
        return {
            'type': 'ir.actions.client',
            'views': [(tree_view_id, 'form')],
            'view_mode': 'form',
            'tag': 'import_offer_template',
            'params': [
                {'model': 'sps.vendor_offer_automation.template', 'offer_id': self.id,
                 'vendor_id': self.partner_id.id,
                 'user_type': 'supplier', 'import_type_ven': 'new_appraisal'}],
        }

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
                    sales_count_index = sales_count_yr_index = sales_total_index = False
                    quantity_index = False
                    price_index = False
                    premium_index = exp_inventory_index = sales_count_90_index = quantity_in_stock_index = False
                    possible_competition_index = False
                    multiplier_index = False
                    credit_index = False
                    potential_profit_margin_index = max_index = False
                    accelerator_index = margin_cost_index = offer_price_index = False
                    offer_price_total_index = retail_price_index = retail_price_total_index = False

                    if 'mf_customer_sku' in mapping_fields:
                        sku_index = excel_columns.index(mapping_fields['mf_customer_sku'])
                    if 'mf_expiration_date' in mapping_fields:
                        expiration_date_index = excel_columns.index(mapping_fields['mf_expiration_date'])
                    if 'mf_uom_ven' in mapping_fields:
                        uom_index = excel_columns.index(mapping_fields['mf_uom_ven'])
                    if 'mf_quantity' in mapping_fields:
                        quantity_index = excel_columns.index(mapping_fields['mf_quantity'])

                    if 'mf_price' in mapping_fields:
                        price_index = excel_columns.index(mapping_fields['mf_price'])
                    # if 'mf_sales_count' in mapping_fields:
                    #     sales_count_index = excel_columns.index(mapping_fields['mf_sales_count'])
                    # if 'mf_sales_count_yr' in mapping_fields:
                    #     sales_count_yr_index = excel_columns.index(mapping_fields['mf_sales_count_yr'])
                    # if 'mf_sales_total' in mapping_fields:
                    #     sales_total_index = excel_columns.index(mapping_fields['mf_sales_total'])
                    # if 'mf_premium' in mapping_fields:
                    #     premium_index = excel_columns.index(mapping_fields['mf_premium'])
                    # if 'mf_exp_inventory' in mapping_fields:
                    #     exp_inventory_index = excel_columns.index(mapping_fields['mf_exp_inventory'])
                    # if 'mf_sales_count_90' in mapping_fields:
                    #     sales_count_90_index = excel_columns.index(mapping_fields['mf_sales_count_90'])
                    # if 'mf_quantity_in_stock' in mapping_fields:
                    #     quantity_in_stock_index = excel_columns.index(mapping_fields['mf_quantity_in_stock'])
                    #
                    # if 'mf_offer_price' in mapping_fields:
                    #     offer_price_index = excel_columns.index(mapping_fields['mf_offer_price'])
                    # if 'mf_offer_price_total' in mapping_fields:
                    #     offer_price_total_index = excel_columns.index(mapping_fields['mf_offer_price_total'])
                    # if 'mf_retail_price' in mapping_fields:
                    #     retail_price_index = excel_columns.index(mapping_fields['mf_retail_price'])
                    # if 'mf_retail_price_total' in mapping_fields:
                    #     retail_price_total_index = excel_columns.index(mapping_fields['mf_retail_price_total'])

                    if 'mf_possible_competition' in mapping_fields:
                        possible_competition_index = excel_columns.index(mapping_fields['mf_possible_competition'])
                    if 'mf_multiplier' in mapping_fields:
                        multiplier_index = excel_columns.index(mapping_fields['mf_multiplier'])
                    # if 'mf_potential_profit_margin' in mapping_fields:
                    #     potential_profit_margin_index = excel_columns.index(
                    #         mapping_fields['mf_potential_profit_margin'])
                    # if 'mf_max' in mapping_fields:
                    #     max_index = excel_columns.index(mapping_fields['mf_max'])
                    #
                    # if 'mf_accelerator' in mapping_fields:
                    #     accelerator_index = excel_columns.index(mapping_fields['mf_accelerator'])
                    if 'mf_credit' in mapping_fields:
                        credit_index = excel_columns.index(mapping_fields['mf_credit'])
                    # if 'mf_margin_cost' in mapping_fields:
                    #     margin_cost_index = excel_columns.index(mapping_fields['mf_margin_cost'])

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
                            price = sales_count = sales_count_yr = sales_total = exp_inventory = sales_count_90 = 0
                            quantity = 1
                            quantity_in_stock = offer_price = offer_price_total = retail_price = retail_price_total = 0
                            possible_competition_name = multiplier_name = margin_cost = 0
                            expiration_date = False
                            uom = ''

                            if price_index and price_index >= 0:
                                price = excel_data_row[price_index]
                            # if sales_count_index and sales_count_index >= 0:
                            #     sales_count = excel_data_row[sales_count_index]
                            # if sales_count_yr_index and sales_count_yr_index >= 0:
                            #     sales_count_yr = excel_data_row[sales_count_yr_index]
                            # if sales_total_index and sales_total_index >= 0:
                            #     sales_total = excel_data_row[sales_total_index]

                            # if exp_inventory_index and exp_inventory_index >= 0:
                            #     exp_inventory = excel_data_row[exp_inventory_index]
                            # if sales_count_90_index and sales_count_90_index >= 0:
                            #     sales_count_90 = excel_data_row[sales_count_90_index]
                            if quantity_index and quantity_index >= 0:
                                quantity = excel_data_row[quantity_index]
                            # if quantity_in_stock_index and quantity_in_stock_index >= 0:
                            #     quantity_in_stock = excel_data_row[quantity_in_stock_index]

                            # if offer_price_index and offer_price_index >= 0:
                            #     offer_price = excel_data_row[offer_price_index]
                            # if offer_price_total_index and offer_price_total_index >= 0:
                            #     offer_price_total = excel_data_row[offer_price_total_index]
                            # if retail_price_index and retail_price_index >= 0:
                            #     retail_price = excel_data_row[retail_price_index]
                            # if retail_price_total_index and retail_price_total_index >= 0:
                            #     retail_price_total = excel_data_row[retail_price_total_index]

                            if possible_competition_index and possible_competition_index >= 0:
                                possible_competition_name = excel_data_row[possible_competition_index]
                            # if multiplier_index and multiplier_index >= 0:
                            #     multiplier_name = excel_data_row[multiplier_index]
                            if count_obj == 0:
                                # if potential_profit_margin_index and potential_profit_margin_index >= 0:
                                #     potential_profit_margin = excel_data_row[potential_profit_margin_index]
                                # if max_index and max_index >= 0:
                                #     max_val = excel_data_row[max_index]
                                # if accelerator_index and accelerator_index >= 0:
                                #     accelerator = excel_data_row[accelerator_index]
                                if credit_index and credit_index >= 0:
                                    credit = excel_data_row[credit_index]

                            if expiration_date_index and expiration_date_index >= 0:
                                expiration_date = excel_data_row[expiration_date_index]
                            if uom_index and uom_index >= 0:
                                uom = excel_data_row[uom_index]
                            # if margin_cost_index and margin_cost_index >= 0:
                            #     margin_cost = excel_data_row[margin_cost_index]

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
                            #query_result = self.env.cr.dictfetchone()
                            query_result = self.env.cr.dictfetchall()
                            if query_result is None and product_sku.startswith("M00"):
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
                                    # for product_obj in products:
                                    #     if product_obj.categ_id and product_obj.categ_id.name == 'EQUIPMENT':
                                    #         raise UserError('This is your alert message.')
                                    if count_obj == 0:
                                        possible_competition = self.env['competition.competition'].search(
                                            [('name', '=', possible_competition_name)]).id
                                    multiplier = self.env['multiplier.multiplier'].search(
                                        [('name', '=', multiplier_name)]).id
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
                                                              product_id=prod_id, qty_in_stock=quantity_in_stock,
                                                              price_unit=offer_price,
                                                              product_retail=0,
                                                              product_unit_price=0, product_offer_price=0,
                                                              product_sales_count_90=sales_count_90,
                                                              product_sales_count_yrs=sales_count_yr,
                                                              product_sales_count=sales_count,
                                                              amount_total_ven_pri=sales_total,
                                                              expired_inventory=exp_inventory,
                                                              offer_price=offer_price, offer_price_total=offer_price_total,
                                                              retail_price=retail_price,
                                                              retail_price_total=retail_price_total,
                                                              possible_competition=possible_competition,
                                                              multiplier=multiplier,
                                                              potential_profit_margin=potential_profit_margin,
                                                              max_val=max_val, accelerator=accelerator, credit=credit,
                                                              margin=margin_cost,
                                                              import_type_ven_line=new_appraisal,
                                                              product_multiple_matches=flag_red,
                                                              list_contains_equip=list_contains_equip
                                                              )
                                        if expiration_date:
                                            order_line_obj.update({'expiration_date': expiration_date})
                                        else:
                                            order_line_obj.update({'expiration_date': None})
                                        if uom:
                                            if uom.upper() == 'EACH':
                                                order_line_obj.update({'uom_str': uom})
                                            if uom.upper() == 'BOX':
                                                uom_obj = products[0].uom_id
                                                temp_qty = uom_obj.factor_inv * float(quantity)
                                                order_line_obj.update({'uom_str': 'each'})
                                                order_line_obj.update({'product_qty': temp_qty})
                                        else:
                                            order_line_obj.update({'uom_str': ''})
                                        order_list_list.append(order_line_obj)
                                        count_obj = count_obj + 1
                                    else:
                                        sku_not_found_list.append(sku_code)
                                        #sku_not_found_list_cleaned.append(sku_code_file)
                            else:
                                sku_not_found_list.append(sku_code)
                                sku_not_found_list_cleaned.append(sku_code_file)

                        # if len(sku_not_found_list) > 0:
                        #     raise ValueError(_("Following SKU does not match \n\n\n %s") % sku_not_found_list)

                        count_order = 0
                        if len(order_list_list) > 0:
                            amount_untaxed = amount_total = 0

                            for order_line_object_add in order_list_list:
                                if order_line_object_add['multiplier'] is False:
                                    order_line_object_add['multiplier'] = None
                                try:
                                    offer_price = float(order_line_object_add['offer_price'])
                                except:
                                    raise ValueError(_("Offer Price  contains incorrect values %s")
                                                     % order_line_object_add['offer_price'])
                                try:
                                    retail_price = float(order_line_object_add['retail_price'])
                                except:
                                    raise ValueError(_("Retail Price  contains incorrect values %s")
                                                     % order_line_object_add['retail_price'])
                                try:
                                    offer_price_total = float(order_line_object_add['offer_price_total'])
                                except:
                                    raise ValueError(_("Offer Price Total  contains incorrect values %s")
                                                     % order_line_object_add['offer_price_total'])
                                try:
                                    retail_price_total = float(order_line_object_add['retail_price_total'])
                                except:
                                    raise ValueError(_("Retail Price Total  contains incorrect values %s")
                                                     % order_line_object_add['retail_price_total'])
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
                                    total_90 = 0
                                    total_yr = 0
                                    total_all = 0
                                    total_m = 0
                                    today_date = datetime.datetime.now()
                                    last_3_months = fields.Date.to_string(today_date - datetime.timedelta(days=90))
                                    last_month = fields.Date.to_string(today_date - datetime.timedelta(days=30))
                                    last_yr = fields.Date.to_string(today_date - datetime.timedelta(days=365))
                                    str_query_cm_new = """
                                                        select sum(sol.qty_delivered) from sale_order AS so JOIN 
                                                        sale_order_line AS sol ON  so.id = sol.order_id where 
                                                        sol.product_id = %s and sol.state in ('sale','done')

                                                       """
                                    self.env.cr.execute(str_query_cm_new + " AND so.date_order>=%s",
                                                        (order_line_object['product_id'], last_3_months))
                                    quant_90 = self.env.cr.fetchone()
                                    if quant_90[0] is not None:
                                        order_line_object['product_sales_count_90'] = int(quant_90[0])


                                    # self.env.cr.execute(str_query_cm_new + " AND so.date_order>=%s",
                                    #                     (order_line_object['product_id'], last_month))
                                    # quant_m = self.env.cr.fetchone()
                                    # if quant_m[0] is not None:
                                    #     order_line_object['product_sales_count_90'] = int(quant_m[0])


                                    self.env.cr.execute(str_query_cm_new + " AND so.date_order>=%s",
                                                        (order_line_object['product_id'], last_yr))
                                    quant_yr = self.env.cr.fetchone()
                                    if quant_yr[0] is not None:
                                        order_line_object['product_sales_count_yrs'] = int(quant_yr[0])


                                    # self.env.cr.execute(str_query_cm_new, [order_line_object['product_id']])
                                    # quant_all = self.env.cr.fetchone()
                                    # if quant_all[0] is not None:
                                    #     order_line_object['product_sales_count_90'] = int(quant_all[0])

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
                                    order_model.write({'possible_competition': possible_competition})
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
                                         " qty_received,state,product_multiple_matches,list_contains_equip)" \
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
                                         " %s,%s,%s,%s) " \
                                         " RETURNING id"

                                sql_query = insert
                                val = (order_line_object['prod_name'], order_line_object['product_uom'],
                                       float("{0:.2f}".format(float(order_line_object['offer_price']))),
                                       order_line_object['product_qty'],  order_line_object['product_qty_app_new'],
                                       order_line_object['date_planned'],
                                       order_line_object['order_id'], order_line_object['product_id'],
                                       order_line_object['qty_in_stock'],
                                       float("{0:.2f}".format(float(order_line_object['retail_price']))),
                                       float("{0:.2f}".format(float(order_line_object['offer_price']))),
                                       order_line_object['product_sales_count']
                                       , order_line_object['product_sales_count_90'],
                                       order_line_object['product_sales_count_yrs'],
                                       order_line_object['expired_inventory'],
                                       float("{0:.2f}".format(float(order_line_object['offer_price_total']))),
                                       order_line_object['multiplier'],
                                       exp_date, order_line_object['uom_str'], exp_date_str,
                                       order_line_object['import_type_ven_line'],
                                       currency_id_insert, 0, create_uid, company_id, create_date, 0, 0, 0, 'true',
                                       'stock_moves',
                                       order_line_object['product_qty'], 0, 'ven_draft',
                                       order_line_object['product_multiple_matches'],
                                       order_line_object['list_contains_equip'])

                                self._cr.execute(sql_query, val)
                                line_obj = self._cr.fetchone()
                                line_order_model = self.env['purchase.order.line'].search(
                                    [('id', 'in', line_obj)])
                                line_order_model.price_subtotal = float(order_line_object['offer_price_total'])

            except UnicodeDecodeError as ue:
                _logger.info(ue)


