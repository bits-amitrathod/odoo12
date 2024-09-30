import datetime
import io
import logging
import re
import time
from odoo import http
from odoo import models, fields, api, _
from odoo.addons.web.controllers.main import  content_disposition
from odoo.exceptions import UserError, ValidationError
from odoo.http import request
from odoo.tools import pycompat

_logger = logging.getLogger(__name__)

try:
    import xlwt
    # add some sanitizations to respect the excel sheet name restrictions
    # as the sheet name is often translatable, can not control the input
    class PatchedWorkbook(xlwt.Workbook):
        def add_sheet(self, name, cell_overwrite_ok=False):
            # invalid Excel character: []:*?/\
            name = re.sub(r'[\[\]:*?/\\]', '', name)

            # maximum size is 31 characters
            name = name[:31]
            return super(PatchedWorkbook, self).add_sheet(name, cell_overwrite_ok=cell_overwrite_ok)
    xlwt.Workbook = PatchedWorkbook

except ImportError:
    xlwt = None

all_field_import = 'all_field_import'

SUPERUSER_ID_INFO = 2


class VendorPricingList(models.Model):
    _inherit = 'product.product'

    product_sales_count = fields.Integer(string="SALES COUNT", readonly=True,
                                         compute='onchange_product_id_vendor_offer_pricing', store=False)
    product_sales_count_month = fields.Integer(string="Sales Count Month", readonly=True,
                                               compute='onchange_product_id_vendor_offer_pricing', store=False)
    product_sales_count_90 = fields.Integer(string="SALES COUNT 90", readonly=True,
                                            compute='onchange_product_id_vendor_offer_pricing', store=False)
    product_sales_count_yrs = fields.Integer(string="SALES COUNT YR", readonly=True,
                                             compute='onchange_product_id_vendor_offer_pricing', store=False)
    qty_in_stock = fields.Integer(string="QTY IN STOCK", readonly=True,
                                  compute='onchange_product_id_vendor_offer_pricing',
                                  store=False)
    expired_inventory = fields.Char(string="EXP INVENTORY", compute='onchange_product_id_vendor_offer_pricing',
                                    readonly=True,
                                    store=False)
    tier_name = fields.Char(string="TIER", readonly=True,
                            compute='onchange_product_id_vendor_offer_pricing',
                            store=False)
    amount_total_ven_pri = fields.Monetary(string='SALES TOTAL', compute='onchange_product_id_vendor_offer_pricing',
                                           readonly=True, store=False)

    inventory_scraped_yr = fields.Char(string='Inventory Scrapped', compute='onchange_product_id_vendor_offer_pricing',
                                       readonly=True, store=False)

    average_aging = fields.Char(string='Average Aging', compute='onchange_product_id_vendor_offer_pricing',
                                readonly=True, store=False)

    quotations_per_code = fields.Integer(string='Open Quotations Per Code',
                                         compute='onchange_product_id_vendor_offer_pricing',
                                         readonly=True, store=False)

    def onchange_product_id_vendor_offer_pricing(self):
        for line in self:
            # if line.product_tmpl_id.tier:
            #     line.product_tier = line.product_tmpl_id.tier
            result1 = {}
            if not line.id:
                return result1

            ''' sale count will show only done qty '''

            total = total_m = total_90 = total_yr = sale_total = 0
            today_date = datetime.datetime.now()
            last_3_months = fields.Date.to_string(today_date - datetime.timedelta(days=90))
            last_month = fields.Date.to_string(today_date - datetime.timedelta(days=30))
            last_yr = fields.Date.to_string(today_date - datetime.timedelta(days=365))
            # cust_location_id = self.env['stock.location'].search([('name', '=', 'Customers')]).id
            sale_order_line = self.env['sale.order.line'].search(
                [('product_id', '=', line.id), ('state', 'in', ('draft', 'sent'))])
            line.quotations_per_code = len(sale_order_line)

            str_query_cm = "SELECT sum(sml.qty_done) FROM sale_order_line AS sol LEFT JOIN stock_picking AS sp ON " \
                           "sp.sale_id=sol.id " \
                           " LEFT JOIN stock_move_line AS sml ON sml.picking_id=sp.id WHERE sml.state='done' AND " \
                           "sml.location_dest_id =%s AND" \
                           " sml.product_id =%s"

            str_query_total_del_qty = """
                select sum(sol.qty_delivered * CAST(coalesce((1.0 / factor), '0') AS integer)) 
                as total_del_qty   from sale_order AS so JOIN sale_order_line AS sol 
                ON so.id = sol.order_id left join uom_uom AS uom on sol.product_uom=uom.id 
                where sol.product_id = %s and sol.state in ('sale','done') 
            """

            ''' state = sale condition added in all sales amount to match the value of sales amount to 
            clients PPvendorpricing file '''

            sale_all_query = """SELECT  sum(sol.price_total) as total_sales
from  product_product pp 
 INNER JOIN sale_order_line sol ON sol.product_id=pp.id 
 INNER JOIN product_template pt ON  pt.id=pp.product_tmpl_id
 INNER JOIN sale_order so ON so.id=sol.order_id
 INNER JOIN stock_picking sp ON sp.sale_id =so.id
 where pp.id =%s and sp.date_done>= %s and sp.date_done<=%s and sp.location_dest_id = 9
  group by sp.state"""

            self.env.cr.execute(sale_all_query, (line.id, last_yr, today_date))

            sales_all_value = 0
            sales_all_val = self.env.cr.fetchone()
            if sales_all_val and sales_all_val[0] is not None:
                sales_all_value = sales_all_value + float(sales_all_val[0])
            line.amount_total_ven_pri = sales_all_value

            # self.env.cr.execute(str_query_cm + " AND sp.date_done>=%s", (cust_location_id,
            #                                                              line.id, last_3_months))
            self.env.cr.execute(str_query_total_del_qty + " AND so.date_order>=%s", (line.id, last_3_months))

            quant_90 = self.env.cr.fetchone()
            if quant_90[0] is not None:
                total_90 = total_90 + int(quant_90[0])
            line.product_sales_count_90 = total_90

            # self.env.cr.execute(str_query_cm + " AND sp.date_done>=%s", (cust_location_id,
            #                                                              line.id, last_month))

            self.env.cr.execute(str_query_total_del_qty + " AND so.date_order>=%s", (line.id, last_month))

            quant_m = self.env.cr.fetchone()
            if quant_m[0] is not None:
                total_m = total_m + int(quant_m[0])
            line.product_sales_count_month = total_m

            # self.env.cr.execute(str_query_cm + " AND sp.date_done>=%s", (cust_location_id,
            #                                                              line.id, last_yr))

            self.env.cr.execute(str_query_total_del_qty + " AND so.date_order>=%s", (line.id, last_yr))

            quant_yr = self.env.cr.fetchone()
            if quant_yr[0] is not None:
                total_yr = total_yr + int(quant_yr[0])
            line.product_sales_count_yrs = total_yr

            # self.env.cr.execute(str_query_cm, (cust_location_id, line.id))
            self.env.cr.execute(str_query_total_del_qty, [line.id])

            quant_all = self.env.cr.fetchone()
            if quant_all[0] is not None:
                total = total + int(quant_all[0])
            line.product_sales_count = total

            self.expired_inventory_cal(line)
            line.qty_in_stock = line.qty_available
            line.tier_name = line.tier.name

            sql_query = """SELECT     Date(PUBLIC.stock_lot.create_date) AS create_date , 
                                                   Sum(PUBLIC.stock_quant.quantity)              AS quantity 
                                        FROM       PUBLIC.product_product 
                                        INNER JOIN PUBLIC.product_template 
                                        ON         ( 
                                                              PUBLIC.product_product.product_tmpl_id = PUBLIC.product_template.id) 
                                        INNER JOIN PUBLIC.stock_lot 
                                        ON         ( 
                                                              PUBLIC.stock_lot.product_id=PUBLIC.product_product.id ) 
                                        INNER JOIN PUBLIC.stock_quant 
                                        ON         ( 
                                                              PUBLIC.stock_quant.lot_id=PUBLIC.stock_lot.id) 
                                        INNER JOIN PUBLIC.stock_location 
                                        ON         ( 
                                                              PUBLIC.stock_location.id=PUBLIC.stock_quant.location_id) 
                                        INNER JOIN PUBLIC.stock_warehouse 
                                        ON         ( 
                                                              PUBLIC.stock_location.id IN (PUBLIC.stock_warehouse.lot_stock_id, 
                                                                                           PUBLIC.stock_warehouse.wh_output_stock_loc_id,
                                                                                           wh_pack_stock_loc_id)) 
                                        WHERE      PUBLIC.stock_quant.quantity>0 
                                        AND        product_template.id = %s  AND stock_lot.use_date >= %s
                                        GROUP BY   PUBLIC.stock_lot.create_date, 
                                                   PUBLIC.product_template.id
                                                   """
            self._cr.execute(sql_query, (line.product_tmpl_id.id, today_date))
            product_lot_list = self.env.cr.dictfetchall()
            sum_qty_day = 0
            total_quantity = 0
            for obj in product_lot_list:
                date_format = "%Y-%m-%d"
                today = fields.date.today().strftime('%Y-%m-%d')
                a = datetime.datetime.strptime(str(today), date_format)
                b = datetime.datetime.strptime(str(obj['create_date']), date_format)
                diff = a - b

                total_quantity = total_quantity + obj['quantity']
                sum_qty_day = sum_qty_day + (obj['quantity'] * diff.days)

            if total_quantity > 0:
                line.average_aging = int(round(sum_qty_day / total_quantity, 0))
            else:
                line.average_aging = 0

            scrapped_list = self.env['stock.scrap'].search([('product_id', '=', line.id), ('state', '=', 'done')
                                                               , ('date_done', '>', last_yr),
                                                            ('date_done', '<', today_date)])
            total_qty = 0
            for obj in scrapped_list:
                total_qty = total_qty + obj.scrap_qty

            line.inventory_scraped_yr = int(total_qty)

    def expired_inventory_cal(self, line):
        expired_lot_count = 0
        test_id_list = self.env['stock.lot'].search([('product_id', '=', line.id)])
        for prod_lot in test_id_list:
            if prod_lot.use_date:
                if fields.Datetime.from_string(prod_lot.use_date).date() < fields.date.today():
                    expired_lot_count = expired_lot_count + 1

        line.expired_inventory = expired_lot_count

    # @api.multi
    def return_tree_vendor_pri(self):
        tree_view_id = self.env.ref('vendor_offer.vendor_pricing_list').id
        action = {
            'name': 'Vendor Pricing',
            'view_mode': 'tree',
            'views': [(tree_view_id, 'tree')],
            'res_model': 'product.product',
            'type': 'ir.actions.act_window',
            'res_id': self.id
        }
        return action

class Product(models.Model):
    _inherit = 'product.template'

    product_note = fields.Text('Note')


#  this global variable is required for storing and fetching values as the list cant be sent using the URL,
#  and the method of ExportPPVendorPricing class will be called from JS file .
product_lines_export_pp = []


class VendorPricingExport(models.TransientModel):
    _name = 'vendor.pricing'
    _description = 'vendor pricing'

    def get_excel_data_vendor_pricing(self):
        today_date = datetime.datetime.now()
        last_yr = fields.Date.to_string(today_date - datetime.timedelta(days=365))
        last_3_months = fields.Date.to_string(today_date - datetime.timedelta(days=90))
        count = 0
        product_lines_export_pp.append((['ProductNumber', 'ProductDescription', 'Price', 'CFP-Manufacturer', 'TIER',
                                         'SALES COUNT', 'SALES COUNT YR', 'QTY IN STOCK', 'SALES TOTAL',
                                         'PREMIUM', 'EXP INVENTORY', 'SALES COUNT 90', 'Quantity on Order',
                                         'Average Aging', 'Inventory Scrapped', 'Open Quotations Per Code']))
        cust_location_id = self.env['stock.location'].search([('name', '=', 'Customers')]).id
        # company = self.env['res.company'].search([], limit=1, order="id desc")
        company = self.env.company
        str_query = """
                        SELECT pt.sku_code, 
                           pt.name, 
                           pt.list_price, 
                           pb.name AS product_brand_id, 
                           tt.name AS tier, 
                           pt.premium, 
                           pp.id, 
                           pp.product_tmpl_id ,
                           CASE 
                             WHEN exp_evntory.name IS NULL THEN '0' 
                             ELSE exp_evntory.name 
                           END     AS expired_lot_count, 
                           CASE 
                             WHEN all_sales.qty_done IS NULL THEN '0' 
                             ELSE all_sales.qty_done 
                           END     AS product_sales_count, 
                           CASE 
                             WHEN yr_sales.qty_done IS NULL THEN '0' 
                             ELSE yr_sales.qty_done 
                           END     AS product_sales_count_yrs, 
                           CASE 
                             WHEN all_sales_amount.total_sales IS NULL THEN '0' 
                             ELSE all_sales_amount.total_sales 
                           END     AS amount_total_ven_pri, 
                           CASE 
                             WHEN ninty_sales.qty_done IS NULL THEN '0' 
                             ELSE ninty_sales.qty_done 
                           END     AS product_sales_count_90,
                           CASE
                           when pt.actual_quantity IS NULL THEN '0' 
                           ELSE pt.actual_quantity end as actual_quantity,
                           CASE 
                             WHEN qty_on_order.product_qty IS NULL THEN '0' 
                             ELSE qty_on_order.product_qty 
                           END     AS qty_on_order,
                           CASE 
                             WHEN inventory_scrapped.scrap_qty IS NULL THEN '0' 
                             ELSE inventory_scrapped.scrap_qty 
                           END     AS scrap_qty ,
                           CASE 
                             WHEN aging.aging_days IS NULL THEN '0' 
                             ELSE aging.aging_days 
                           END     AS aging_days ,
                             CASE 
                             WHEN quotations_per_code.quotation_count IS NULL THEN '0' 
                             ELSE quotations_per_code.quotation_count
                           END     AS quotations_per_code

                    FROM   product_product pp 
                           inner join product_template pt 
                                   ON pp.product_tmpl_id = pt.id 
                                      AND pt.TYPE = 'product' 
                           left join tier_tier tt 
                                  ON pt.tier = tt.id 
                           left join product_brand pb 
                                  ON pt.product_brand_id = pb.id 
                          left join (select sum(sol.qty_delivered * CAST(coalesce((1.0 / factor), '0') AS integer)) AS qty_done,sol.product_id
                                   from sale_order AS so JOIN sale_order_line AS sol ON
                                   so.id = sol.order_id 
                                   left join uom_uom AS uom on sol.product_uom=uom.id
                                   where  
                                   sol.state in ('sale','done') 
                                  GROUP BY  sol.product_id) AS all_sales 
                                  ON pp.id = all_sales.product_id 
                           left join (SELECT CASE 
                                               WHEN Abs(SUM(sol.qty_delivered * sol.price_reduce)) IS NULL THEN 0 
                                               ELSE Abs(SUM(sol.qty_delivered * sol.price_reduce)) 
                                             END AS total_sales, 
                                             ppi.id

                                      FROM   product_product ppi 
                                             inner join sale_order_line sol 
                                                     ON sol.product_id = ppi.id  and sol.state NOT IN ('cancel','void')
                                             inner join product_template pt 
                                                     ON pt.id = ppi.product_tmpl_id 
                                             inner join sale_order so 
                                                     ON so.id = sol.order_id 
                                             INNER JOIN stock_picking sp ON sp.sale_id =so.id
                                     WHERE   sp.date_done >= %s and sp.location_dest_id = 9
                                             AND sp.state IN ('done') 
                                      GROUP  BY ppi.id) AS all_sales_amount 
                                  ON all_sales_amount.id = pp.id 
                            left join (select sum(sol.qty_delivered * CAST(coalesce((1.0 / factor), '0') AS integer)) AS qty_done,sol.product_id
                                   from sale_order AS so JOIN sale_order_line AS sol ON
                                   so.id = sol.order_id  
                                   left join uom_uom AS uom on sol.product_uom=uom.id
                                   where  
                                   sol.state in ('sale','done')
                                   and so.date_order >= %s 
                                  GROUP BY  sol.product_id ) AS yr_sales 
                                  ON pp.id = yr_sales.product_id 

                             left join(SELECT ppc.id,count(ppc.id) as quotation_count 
                                    from  product_product ppc   
                                       INNER JOIN sale_order_line soli ON soli.product_id=ppc.id 
                                       INNER JOIN product_template pti ON  pti.id=ppc.product_tmpl_id 
                                       INNER JOIN sale_order sor ON sor.id=soli.order_id   
                                        where sor.state in ('draft','sent')   
                                           GROUP  BY ppc.id) AS quotations_per_code
                                           on pp.id =  quotations_per_code.id

                          LEFT JOIN ( 
                         select  case when sum(quantity) = 0 then 0 else round(cast (sum(sum_qty_day)/sum(quantity) as numeric),0) end   as aging_days,pt_id as pt_id  from
									( SELECT     date_part('day', now() -  Date(PUBLIC.stock_lot.create_date)) as diff, 
                                                       Sum(PUBLIC.stock_quant.quantity)              AS quantity ,
										Sum(PUBLIC.stock_quant.quantity)  * date_part('day', now() -  Date(PUBLIC.stock_lot.create_date)) as sum_qty_day,
																	PUBLIC.product_template.id	as pt_id						   
                                            FROM       PUBLIC.product_product 
                                            INNER JOIN PUBLIC.product_template 
                                            ON         ( 
                                                                  PUBLIC.product_product.product_tmpl_id = PUBLIC.product_template.id) 
                                            INNER JOIN PUBLIC.stock_lot 
                                            ON         ( 
                                                                  PUBLIC.stock_lot.product_id=PUBLIC.product_product.id ) 
                                            INNER JOIN PUBLIC.stock_quant 
                                            ON         ( 
                                                                  PUBLIC.stock_quant.lot_id=PUBLIC.stock_lot.id) 
                                            INNER JOIN PUBLIC.stock_location 
                                            ON         ( 
                                                                  PUBLIC.stock_location.id=PUBLIC.stock_quant.location_id) 
                                            INNER JOIN PUBLIC.stock_warehouse 
                                            ON         ( 
                                                                  PUBLIC.stock_location.id IN (PUBLIC.stock_warehouse.lot_stock_id, 
                                                                                               PUBLIC.stock_warehouse.wh_output_stock_loc_id,
                                                                                               wh_pack_stock_loc_id)) 
                                            WHERE      PUBLIC.stock_quant.quantity>0 AND PUBLIC.stock_lot.use_date >= %s

                                            GROUP BY   PUBLIC.stock_lot.create_date, 
                                                       PUBLIC.product_template.id ) as all_rec

												 GROUP BY pt_id 
								) as aging  on aging.pt_id = pp.product_tmpl_id 

								"""

        str_query_join = """  

                                LEFT JOIN 
                        ( 
                                  select sum(sol.qty_delivered * CAST(coalesce((1.0 / factor), '0') AS integer)) AS qty_done,sol.product_id
                                   from sale_order AS so JOIN sale_order_line AS sol ON
                                   so.id = sol.order_id 
                                   left join uom_uom AS uom on sol.product_uom=uom.id
                                   where
                                   sol.state in ('sale','done')
                                   and so.date_order >= %s 
                                  GROUP BY  sol.product_id
                           ) AS ninty_sales ON pp.id=ninty_sales.product_id LEFT JOIN 
                        ( 
                                 SELECT   count(spl.NAME) AS NAME, 
                                          spl.product_id 
                                 FROM     stock_lot spl 
                                 WHERE    spl.use_date < %s 
                                 GROUP BY spl.product_id ) AS exp_evntory ON pp.id=exp_evntory.product_id LEFT JOIN 
                        ( 
                                   SELECT     sum(sq.quantity) AS qty_available, 
                                              spl.product_id 
                                   FROM       stock_quant sq 
                                   INNER JOIN stock_lot AS spl 
                                   ON         sq.lot_id = spl.id 
                                   INNER JOIN stock_location AS sl 
                                   ON         sq.location_id = sl.id 
                                   WHERE      sl.usage IN ('internal', 
                                                           'transit') 
                                   GROUP BY   spl.product_id ) AS qty_available_count ON pp.id=qty_available_count.product_id LEFT JOIN
                        ( 
                                 SELECT   "stock_move"."product_id"       AS "product_id", 
                                          sum("stock_move"."product_qty") AS "product_qty" 
                                 FROM     "stock_location"                AS "stock_move__location_dest_id", 
                                          "stock_location"                AS "stock_move__location_id", 
                                          "stock_move" 
                                 WHERE    ( 
                                                   "stock_move"."location_id" = "stock_move__location_id"."id" 
                                          AND      "stock_move"."location_dest_id" = "stock_move__location_dest_id"."id")
                                 AND      (((( 
                                                                              "stock_move"."state" IN('waiting', 
                                                                                                      'confirmed', 
                                                                                                      'assigned', 
                                                                                                      'partially_available')) )
                                                   AND      ( 
                                                                     "stock_move__location_dest_id"."parent_path" :: text LIKE '1/11/%%' ))
                                          AND      ( 
                                                            NOT(( 
                                                                              "stock_move__location_id"."parent_path" :: text LIKE '1/11/%%' )) ))
                                 AND      ( 
                                                   "stock_move"."company_id" IS NULL 
                                          OR       ( 
                                                            "stock_move"."company_id" IN(""" + str(company.id) + """))) 
                                 GROUP BY "stock_move"."product_id" ) AS qty_on_order ON pp.id=qty_on_order.product_id LEFT JOIN
                        ( 
                                 SELECT   sum(sts.scrap_qty) AS scrap_qty, 
                                          sts.product_id 
                                 FROM     stock_scrap sts 
                                 WHERE    sts.state ='done' 
                                 AND      sts.date_done < %s 
                                 AND      sts.date_done > %s 
                                 GROUP BY sts.product_id ) AS inventory_scrapped ON pp.id=inventory_scrapped.product_id WHERE pp.active=true  """

        start_time = time.time()
        self.env.cr.execute(str_query + str_query_join,
                            (last_yr, last_yr, today_date,
                             last_3_months, today_date,
                             today_date, last_yr))

        new_list = self.env.cr.dictfetchall()

        for line in new_list:
            # count = count + 1  # for printing count if needed
            # self.env.cr.execute("select get_aging_days(" + str(line['product_tmpl_id']) + ")")
            # aging_days = self.env.cr.fetchone()
            product_lines_export_pp.append(
                ([line['sku_code'], line['name'], line['list_price'], line['product_brand_id'],
                  line['tier'], line['product_sales_count'], line['product_sales_count_yrs'],
                  line['actual_quantity'], line['amount_total_ven_pri'], line['premium'],
                  line['expired_lot_count'], line['product_sales_count_90'], line['qty_on_order'],
                  line['aging_days'], line['scrap_qty'], line['quotations_per_code']]))

        print("--- %s seconds ---" % (time.time() - start_time))

        ''' code for writing csv file in default location in odoo 

        with open(file_name, 'w', newline='') as fp:
            a = csv.writer(fp, delimiter=',')
            data_lines = product_lines
            a.writerows(data_lines)
        print('---------- time required ----------')
        print(datetime.datetime.now() - today_date)  '''

        return product_lines_export_pp

    def download_excel_ven_price(self):
        list_val = self.get_excel_data_vendor_pricing()
        if list_val and len(list_val) > 0:
            return {
                'type': 'ir.actions.act_url',
                'url': '/web/PPVendorPricing/download_document_xl',
                'target': 'new'
            }
        else:
            product_lines_export_pp.clear()
            raise UserError(
                _('Cannot Export at the moment ,Please try after sometime.'))


class ExportPPVendorPricingCSV(http.Controller):

    #   Custom code for fast export , existing code uses ORM ,so it is slow
    #   Only CSV will be exported as per requirement

    @property
    def content_type(self):
        return 'text/csv'

    def filename(self):

        #  code for custom date in file name if required
        #
        #                str_date = today_date.strftime("%m_%d_%Y_%H_%M_%S")
        #                file_name = 'PPVendorPricing_' + str_date + '.csv'
        #
        #

        #   Only CSV will be exported as per requirement
        return 'PPVendorPricing' + '.csv'

    def from_data(self, rows):
        fp = io.BytesIO()
        writer = pycompat.csv_writer(fp, quoting=1)
        for data in rows:
            row = []
            for d in data:
                if isinstance(d, pycompat.string_types) and d.startswith(('=', '-', '+')):
                    d = "'" + d

                row.append(pycompat.to_text(d))
            writer.writerow(row)

        return fp.getvalue()

    @http.route('/web/PPVendorPricing/download_document', type='http', auth="public")
    # @serialize_exception
    def download_document(self, token=1, debug=1):

        #  token=1,debug=1   are added if the URL contains extra parameters , which in some case URL does contain
        #  code will produce error if the parameters are not provided so default are added

        res = request.make_response(self.from_data(product_lines_export_pp),
                                    headers=[('Content-Disposition',
                                              content_disposition(self.filename())),
                                             ('Content-Type', self.content_type)],
                                    )
        product_lines_export_pp.clear()
        return res


class ExportPPVendorPricingXL(http.Controller):

    #   Custom code for fast export , existing code uses ORM ,so it is slow
    #   XL will be

    @property
    def content_type(self):
        return 'application/vnd.ms-excel'

    def filename(self):

        #  code for custom date in file name if required
        #
        #                str_date = today_date.strftime("%m_%d_%Y_%H_%M_%S")
        #                file_name = 'PPVendorPricing_' + str_date + '.xls'
        #   XL will be exported
        return 'PPVendorPricing' + '.xls'

    def from_data(self, field, rows):
        try:
            if len(rows) > 65535:
                raise UserError(_(
                    'There are too many rows (%s rows, limit: 65535) to export as Excel 97-2003 (.xls) format. Consider splitting the export.') % len(
                    rows))

            workbook = xlwt.Workbook()
            worksheet = workbook.add_sheet('Sheet 1')

            for i, fieldname in enumerate(field):
                worksheet.write(0, i, fieldname)
                if i == 1:
                    worksheet.col(i).width = 20000  #
                else:
                    worksheet.col(i).width = 4000  # around 110 pixels

            base_style = xlwt.easyxf('align: wrap yes')
            date_style = xlwt.easyxf('align: wrap yes', num_format_str='YYYY-MM-DD')
            datetime_style = xlwt.easyxf('align: wrap yes', num_format_str='YYYY-MM-DD HH:mm:SS')

            for row_index, row in enumerate(rows):
                for cell_index, cell_value in enumerate(row):
                    cell_style = base_style

                    if isinstance(cell_value, bytes) and not isinstance(cell_value, pycompat.string_types):
                        # because xls uses raw export, we can get a bytes object
                        # here. xlwt does not support bytes values in Python 3 ->
                        # assume this is base64 and decode to a string, if this
                        # fails note that you can't export
                        try:
                            cell_value = pycompat.to_text(cell_value)
                        except UnicodeDecodeError:
                            raise UserError(_(
                                "Binary fields can not be exported to Excel unless their content is base64-encoded. That does not seem to be the case for %s.") %
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
        except Exception as ex:
            _logger.error("Error", ex)

    @http.route('/web/PPVendorPricing/download_document_xl', type='http', auth="public")
    # @serialize_exception
    def download_document_xl(self, token=1, debug=1):

        #  token=1,debug=1   are added if the URL contains extra parameters , which in some case URL does contain
        #  code will produce error if the parameters are not provided so default are added
        try:


            res = request.make_response(self.from_data(product_lines_export_pp[0], product_lines_export_pp[1:]),
                                        headers=[('Content-Disposition',
                                                  content_disposition(self.filename())),
                                                 ('Content-Type', self.content_type)],
                                        )
            product_lines_export_pp.clear()
            return res

        except:
            res = request.make_response('', '')
            product_lines_export_pp.clear()
            return res

