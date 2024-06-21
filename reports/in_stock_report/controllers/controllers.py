# -*- coding: utf-8 -*-
import datetime

import math
from odoo import http, _, fields
from odoo.addons.web.controllers.main import content_disposition
from odoo.exceptions import UserError
from odoo.http import request
from odoo.tools import pycompat, io, re, xlwt


class ReportPrintInStockExport(http.Controller):

    def from_data(self, field, rows):
        split_data = []
        limit = 65530
        # 65535
        if len(rows) > limit:
            count = math.ceil(len(rows) / limit)
            index = 0
            max = limit
            for loop in range(count):
                split_data.append(rows[index:max])
                index = index + limit
                max = max + limit
        else:
            split_data.append(rows)

        workbook = xlwt.Workbook()
        count = 1
        for data in split_data:
            worksheet = workbook.add_sheet('Sheet ' + str(count))
            count = count + 1

            for i, fieldname in enumerate(field):
                worksheet.write(0, i, fieldname)
                if i == 3:
                    worksheet.col(i).width = 22000  #
                else:
                    worksheet.col(i).width = 4500  # around 110 pixels
                if i == 0:
                    worksheet.col(i).width = 13000

            base_style = xlwt.easyxf('align: wrap yes')
            date_style = xlwt.easyxf('align: wrap yes', num_format_str='YYYY-MM-DD')
            datetime_style = xlwt.easyxf('align: wrap yes', num_format_str='YYYY-MM-DD HH:mm:SS')

            for row_index, row in enumerate(data):
                for cell_index, cell_value in enumerate(row):
                    cell_style = base_style

                    if isinstance(cell_value, bytes) and not isinstance(cell_value, str):

                        try:
                            cell_value = pycompat.to_text(cell_value)
                        except UnicodeDecodeError:
                            raise UserError(_(
                                "Binary fields can not be exported to Excel unless their content is base64-encoded. That "
                                "does not seem to be the case for %s.") %
                                            fields[cell_index])

                    if isinstance(cell_value, str):
                        cell_value = re.sub("\r", " ", pycompat.to_text(cell_value))
                        # Excel supports a maximum of 32767 characters in each cell:
                        cell_value = cell_value[:32767]
                    elif isinstance(cell_value, datetime.datetime):
                        cell_style = datetime_style
                    elif isinstance(cell_value, datetime.date):
                        cell_style = date_style
                    elif isinstance(cell_value, dict) and 'en_US' in cell_value:
                        cell_value = cell_value.get('en_US') or cell_value.get(list(cell_value.keys())[0]) or ''

                    worksheet.write(row_index + 1, cell_index, cell_value, cell_style)

        fp = io.BytesIO()
        workbook.save(fp)
        fp.seek(0)
        data = fp.read()
        fp.close()
        return data

    @http.route('/web/export/in_stock_report', type='http', auth="public")
    def download_document_xl(self, token, **kwargs):

        """
          DROP VIEW DATA;
          DROP FUNCTION list_price_val(integer,integer,double precision);
            DROP FUNCTION getPricelist(integer);
               DROP FUNCTION  cal_price_rule (integer,varchar,integer,integer,integer) ;
        """
        str_functions = """	 
             CREATE OR REPLACE FUNCTION getPricelist (partner_id_param integer)  
                RETURNS integer AS $price_list_id$  
                declare  
                    price_list_id_val integer;  
                    compnay_id_param integer;  
                BEGIN

                                select company_id INTO  compnay_id_param from res_partner where id=partner_id_param;
                                SELECT r.id INTO price_list_id_val FROM ir_property p
                                LEFT JOIN product_pricelist r ON substr(p.value_reference, 19)::integer=r.id
                                WHERE p.name='property_product_pricelist'
                                    AND (p.company_id=compnay_id_param OR p.company_id IS NULL)
                                    AND (p.res_id IN ('res.partner,'||partner_id_param) OR p.res_id IS NULL)
                                ORDER BY p.company_id NULLS FIRST;

                            IF price_list_id_val is not null THEN
                            RETURN price_list_id_val; 
                            ELSE 

                                        select pp.id as price_list_id into price_list_id_val  from product_pricelist pp left join
                                        res_country_group_pricelist_rel rec
                                        on  pp.id = rec.pricelist_id left join res_country_res_country_group_rel rel
                                        on  rec.res_country_group_id= rel.res_country_group_id right join 	res_partner	resp
                                        on resp.country_id= rel.res_country_id    where resp.id =partner_id_param;

                                    IF price_list_id_val is not null THEN
                                    RETURN price_list_id_val; 
                                    ELSE 
                                           select id from product_pricelist into price_list_id_val where id not in  
                                          (select pricelist_id from res_country_group_pricelist_rel) order by id  limit 1;

                                            IF price_list_id_val is not null THEN
                                                  RETURN price_list_id_val; 
                                            ELSE  
                                                  select id from product_pricelist  into price_list_id_val order by id  limit 1;
                                            END IF;

                                    END IF;
                            END IF;

                RETURN price_list_id_val;  
                END;  
                $price_list_id$ LANGUAGE plpgsql; 


                CREATE OR REPLACE FUNCTION cal_price_rule (id_param integer,compute_price_param varchar,product_id_param integer,pricelist_param integer,product_tmpl_id_param integer)  
                RETURNS numeric AS $list_price_return$  
                declare  
                    list_price_return_val float8; 
                    percentage_price_val float8; 
                    list_price_val float8; 
                    price_limit_val float8;
                    price_limit_val_for_min float8;
                    price_limit_val_for_max float8;
                    price_discount_val float8;
                    price_round_val float8;
                    price_surcharge_val float8;
                    price_min_margin_val float8;
                    price_max_margin_val float8;

                BEGIN  
                            IF compute_price_param ='fixed' THEN
                            select fixed_price INTO list_price_return_val  from product_pricelist_item where id = id_param limit 1;
                            RETURN list_price_return_val;
                            ELSE 
                                  IF compute_price_param ='percentage' THEN
                                    select percent_price INTO percentage_price_val  from product_pricelist_item where id = id_param limit 1;
                                    select case list_price when null then '0' else list_price end as list_price INTO list_price_val from product_template  where id=product_tmpl_id_param and  product_template.sale_ok = True;
                                    IF list_price_val is null then
                                        list_price_val =0;
                                    END IF;
                                   list_price_return_val = (list_price_val - (list_price_val * (percentage_price_val / 100)));
                                    RETURN list_price_return_val;
                                  ELSE
                                        IF compute_price_param ='formula' THEN

                                        END IF;
                                  END IF;

                            END IF;

                RETURN list_price_return_val;  
                END;  
                $list_price_return$ LANGUAGE plpgsql; 

                  CREATE OR REPLACE FUNCTION list_price_val (partner_id_param integer,product_id_param integer,actual_quantity_param float8)  
                RETURNS numeric AS $list_price_return$  
                declare  
                     list_price_return_val float8;  
                     product_tmpl_id_param integer;  
                     categ_id_param integer;
                     pricelist_param integer;

                BEGIN  		pricelist_param = getPricelist(partner_id_param);
                            select product_tmpl_id INTO product_tmpl_id_param from product_product where id=product_id_param;
                            select categ_id INTO categ_id_param from product_template where id=product_tmpl_id_param and product_template.sale_ok = True;

                                select cal_price_rule(id,compute_price,product_id_param,pricelist_param,product_tmpl_id_param) INTO list_price_return_val  from product_pricelist_item 
                                where pricelist_id = pricelist_param and product_id = product_id_param and min_quantity <= actual_quantity_param
                                and (date_start is null OR date_start <= now()) and (date_end is null OR date_end >= now())   order by min_quantity desc ,id limit 1;

                            IF list_price_return_val is not null THEN
                                RETURN list_price_return_val; 
                            ELSE 


                                 select cal_price_rule(id,compute_price,product_id_param,pricelist_param,product_tmpl_id_param) INTO list_price_return_val from product_pricelist_item
                                    where pricelist_id = pricelist_param and  product_tmpl_id = product_tmpl_id_param and min_quantity <= actual_quantity_param
                                    and (date_start is null OR date_start <= now()) and (date_end is null OR date_end >= now())
                                     order by min_quantity desc ,id limit 1;

                                    IF list_price_return_val is not null THEN
                                        RETURN list_price_return_val; 
                                    ELSE
                                            select cal_price_rule(id,compute_price,product_id_param,pricelist_param,product_tmpl_id_param) INTO list_price_return_val  from product_pricelist_item 
                                            where pricelist_id = pricelist_param and categ_id = categ_id_param and min_quantity <= actual_quantity_param
                                            and (date_start is null OR date_start <= now()) and (date_end is null OR date_end >= now())  order by min_quantity desc ,id limit 1;

                                            IF list_price_return_val is not null THEN
                                                RETURN list_price_return_val; 
                                            ELSE
                                                    select  cal_price_rule(id,compute_price,product_id_param,pricelist_param,product_tmpl_id_param) INTO list_price_return_val  from product_pricelist_item 
                                                    where pricelist_id = pricelist_param and applied_on = '3_global' and min_quantity <= actual_quantity_param
                                                    and (date_start is null OR date_start <= now()) and (date_end is null OR date_end >= now())  order by min_quantity desc ,id limit 1;
                                            END IF;

                                    END IF;

                            END IF;

                IF list_price_return_val is  null THEN
                    select list_price INTO list_price_return_val from product_template where id=product_tmpl_id_param and product_template.sale_ok = True;
                        IF list_price_return_val is  null THEN
                        RETURN 0; 
                    ELSE 
                        RETURN list_price_return_val;
                    END IF;
                ELSE
                    RETURN list_price_return_val;  
                END IF;
                END;  
                $list_price_return$ LANGUAGE plpgsql; 


                CREATE OR REPLACE FUNCTION is_pricelist_formula (partner_id_param integer,product_id_param integer,actual_quantity_param float8)  
                RETURNS numeric AS $list_price_return$  
                declare  
                     list_price_return_val float8;  
                     product_tmpl_id_param integer;  
                     categ_id_param integer;
                     pricelist_param integer;

                BEGIN  		
                        pricelist_param = getPricelist(partner_id_param);
                        select product_tmpl_id INTO product_tmpl_id_param from product_product where id=product_id_param;
                        select categ_id INTO categ_id_param from product_template where id=product_tmpl_id_param and product_template.sale_ok = True;

                         select get_formula_rule(id,compute_price,product_id_param,pricelist_param,product_tmpl_id_param) INTO list_price_return_val  from product_pricelist_item 
                            where pricelist_id = pricelist_param and product_id = product_id_param and min_quantity <= actual_quantity_param
                            and (date_start is null OR date_start <= now()) and (date_end is null OR date_end >= now())   order by min_quantity desc ,id limit 1;


                        IF list_price_return_val is not null THEN
                            RETURN list_price_return_val; 
                        ELSE 

                                      select get_formula_rule(id,compute_price,product_id_param,pricelist_param,product_tmpl_id_param) INTO list_price_return_val from product_pricelist_item
                                        where pricelist_id = pricelist_param and  product_tmpl_id = product_tmpl_id_param and min_quantity <= actual_quantity_param
                                        and (date_start is null OR date_start <= now()) and (date_end is null OR date_end >= now())
                                        order by min_quantity desc ,id limit 1	;
                                IF list_price_return_val is not null THEN
                                    RETURN list_price_return_val; 
                                ELSE
                                           select get_formula_rule(id,compute_price,product_id_param,pricelist_param,product_tmpl_id_param) INTO list_price_return_val  from product_pricelist_item 
                                            where pricelist_id = pricelist_param and categ_id = categ_id_param and min_quantity <= actual_quantity_param
                                            and (date_start is null OR date_start <= now()) and (date_end is null OR date_end >= now()) order by min_quantity desc ,id limit 1 ;

                                        IF list_price_return_val is not null THEN
                                            RETURN list_price_return_val; 
                                        ELSE
                                                select  get_formula_rule(id,compute_price,product_id_param,pricelist_param,product_tmpl_id_param) INTO list_price_return_val  from product_pricelist_item 
                                                where pricelist_id = pricelist_param and applied_on = '3_global' and min_quantity <= actual_quantity_param
                                                and (date_start is null OR date_start <= now()) and (date_end is null OR date_end >= now())  order by min_quantity desc ,id limit 1;
                                        END IF;

                                END IF;

                        END IF;

                 IF list_price_return_val is  null THEN
                    RETURN 0;  
                 ELSE
                    RETURN list_price_return_val;  
                 END IF;

                END;  
                $list_price_return$ LANGUAGE plpgsql; 

                CREATE OR REPLACE FUNCTION get_formula_rule (id_param integer,compute_price_param varchar,product_id_param integer,pricelist_param integer,product_tmpl_id_param integer)  
                RETURNS numeric AS $list_price_return$  
                declare  
                BEGIN  
                        IF compute_price_param ='formula' THEN
                            RETURN 1;
                        ELSE 
                            RETURN 0; 
                        END IF;
                END;  
                $list_price_return$ LANGUAGE plpgsql; 

        """

        str_query0 = """
        create or replace TEMPORARY VIEW data AS 
        SELECT
          CONCAT(sale_order.partner_id, product_product.id) as id,
          public.res_partner.name as res_partner,
          public.product_brand.name as product_brand,
          public.product_template.sku_code,
          public.product_template.name as product_template,
          public.uom_uom.name as product_uom,
          public.sale_order_line.product_id,
          sale_order.partner_id,
          public.product_template.actual_quantity
          """
        str_query1 = """
                create or replace TEMPORARY VIEW data AS 
                SELECT
                 distinct(  CONCAT(sale_order.partner_id, product_product.id)) as id,
                  public.res_partner.name as res_partner,
                  public.product_brand.name as product_brand,
                  public.product_template.sku_code,
                  public.product_template.name as product_template,
                  public.uom_uom.name as product_uom,
                  public.sale_order_line.product_id,
                  sale_order.partner_id,
                  public.product_template.actual_quantity
                  """
        str_query2 = """
        ,
          list_price_val(sale_order.partner_id,product_product.id,public.product_template.actual_quantity) as list_price
          , CAST ('0' AS numeric)  as formula
        """
        str_query3 = """
        ,  CAST ('0' AS numeric) as list_price, 
        is_pricelist_formula(sale_order.partner_id,product_product.id,public.product_template.actual_quantity) as formula
          """
        str_query4 = """

        FROM
          public.sale_order 
          INNER JOIN
            public.sale_order_line 
            ON ( public.sale_order.id = public.sale_order_line.order_id) 
          INNER JOIN
            public.product_product 
            ON ( public.sale_order_line.product_id = public.product_product.id) 
          INNER JOIN
            public.product_template 
            ON ( public.product_product.product_tmpl_id = public.product_template.id and public.product_template.sale_ok = True) 
          INNER JOIN
            public.res_partner 
            ON ( public.sale_order.partner_id = public.res_partner.id) 
          LEFT JOIN
            public.product_brand 
            ON ( public.product_template.product_brand_id = public.product_brand.id) 
          INNER JOIN
            public.uom_uom 
            ON ( public.product_template.uom_id = public.uom_uom.id) 
        WHERE
          product_template.actual_quantity > 0;

        create  or replace TEMPORARY VIEW data2 AS 
        SELECT
          min(use_date) as min_expiration_date,
          max(use_date) as max_expiration_date,
          stock_lot.product_id 
        FROM
          stock_quant 
          INNER JOIN
            stock_lot 
            ON ( stock_quant.lot_id = stock_lot.id) 
          INNER JOIN
            stock_location 
            ON ( stock_quant.location_id = stock_location.id) 
        WHERE stock_location.usage in ( 'internal', 'transit')
        group by
          stock_lot.product_id;

        select
          * 
        from
          data 
          left JOIN
            data2 
            ON ( data.product_id = data2.product_id )
        """

        request.env.cr.execute(str_functions + str_query0 + str_query2 + str_query4)
        order_lines = request.env.cr.dictfetchall()
        request.env.cr.execute(str_query1 + str_query3 + str_query4 + "where formula = 1")
        order_lines_formula = request.env.cr.dictfetchall()

        data = {}
        data_formula = {}
        # print("-------------1------------")
        # print(len(order_lines))
        count = 0
        for line in order_lines:
            if not line['id'] in data:
                data[line['id']] = line

        for line in order_lines_formula:
            if not line['id'] in data_formula:
                data_formula[line['id']] = line

        records = []

        for line in data_formula.values():
            partner_id = request.env['res.partner'].browse(line['partner_id'])
            product_id = request.env['product.product'].browse(line['product_id'])
            if product_id:
                if partner_id.property_product_pricelist.id:
                    line['list_price'] = partner_id.property_product_pricelist._get_product_price(product_id, line['actual_quantity'])
            data[line['id']] = line

        for line in data.values():
            # if line['formula'] == 1:
            #     partner_id = request.env['res.partner'].browse(line['partner_id'])
            #     product_id = request.env['product.product'].browse(line['product_id'])
            #     if product_id:
            #         if partner_id.property_product_pricelist.id:
            #             line['list_price'] = partner_id.property_product_pricelist._get_product_price(product_id, line['actual_quantity'])
            records.append([line['res_partner'], line['product_brand'], line['sku_code'], line['product_template'],
                            "$" + " {0:.2f}".format(line['list_price']), line['actual_quantity'], line['product_uom'],
                            line['min_expiration_date'], line['max_expiration_date']])

        res = request.make_response(
            self.from_data(["partner_name", "brand_name", "sku_code", "product_name", "price_list"
                               , "actual_quantity", "product_uom", "min_expiration_date", "max_expiration_date"],
                           records),
            headers=[('Content-Disposition', content_disposition('in_stock_report' + '.xls')),
                     ('Content-Type', 'application/vnd.ms-excel')],
        )
        res.set_cookie('fileToken', token)

        return res