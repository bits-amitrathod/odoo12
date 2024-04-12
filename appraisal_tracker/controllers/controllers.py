# -*- coding: utf-8 -*-
import datetime
import math
from odoo import http, _, fields
from odoo.addons.web.controllers.main import content_disposition
from odoo.exceptions import UserError
from odoo.http import request
from odoo.tools import pycompat, io, re, xlwt


class ApprisalTracker(http.Controller):
    @http.route('/apprisal_tracker/apprisal_tracker/', auth='public')
    def index(self, **kw):
        return "Hello, world"

    @http.route('/apprisal_tracker/apprisal_tracker/objects/', auth='public')
    def list(self, **kw):
        return http.request.render('apprisal_tracker.listing', {
            'root': '/apprisal_tracker/apprisal_tracker',
            'objects': http.request.env['apprisal_tracker.apprisal_tracker'].search([]),
        })

    @http.route('/apprisal_tracker/apprisal_tracker/objects/<model("apprisal_tracker.apprisal_tracker"):obj>/',
                auth='public')
    def object(self, obj, **kw):
        return http.request.render('apprisal_tracker.object', {
            'object': obj
        })

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
                if i == 2:
                    worksheet.col(i).width = 13000  #
                elif i == 1:
                    worksheet.col(i).width = 5000  #
                else:
                    worksheet.col(i).width = 4700  # around 110 pixels

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
                    elif isinstance(cell_value,dict):
                        cell_value = cell_value.get('en_US') or cell_value.get(list(cell_value.keys())[0]) or ''
                    worksheet.write(row_index + 1, cell_index, cell_value, cell_style)

        fp = io.BytesIO()
        workbook.save(fp)
        fp.seek(0)
        data = fp.read()
        fp.close()
        return data

    @http.route('/web/export/appraisal_xl', type='http', auth="public")
    def download_document_xl(self, token=1, debug=1):

        str_functions = """	 

                     select distinct po.name as po , po.appraisal_no,acq_man.name as acq_manager,rp.name as facility,
                     rp.saleforce_ac as vendor_cust_id,po.final_billed_offer_total,po.final_billed_retail_total,
                    case when  rp.is_wholesaler = true then 'Wholesaler' 
                    when  rp.charity = true then 'Charity' 
                    when  rp.is_broker = true then 'Broker' 
                    else  'Traditional' end as ap_type, 
                      apt.name as payment_term,
                      amount.total_offer,amount.total_retail,amount.billed_offer,amount.billed_retail,po.create_date,
                      po.shipping_label_issued , po.shipping_date, 
                                po.delivered_date, po.arrival_date_grp,
                    case when po.new_customer = True then 'Yes' else 'No' end as  new_customer,
                    case when po.state in ('ven_draft','ven_sent')  and  (po.arrival_date_grp is  null) then 'Vendor Offer'
					when po.state ='purchase' and po.arrival_date_grp  is null  and date_done.date_done is  null
					and po.invoice_status !='invoiced'
					then 'Accepted'
					when po.state ='cancel'  then 'Declined'
					when po.arrival_date_grp is not null  and po.state !='cancel'  and  po.invoice_status !='invoiced' then 'Arrived'
                                        when date_done.date_done is not null  and po.invoice_status !='invoiced' 
                                        and  po.state !='cancel' then 'Checked Into Inventory' 
					when po.invoice_status ='invoiced' and po.state !='cancel' then 'Bill created'
					end as status ,
					case when po.tier1_extra_retail > 0 THEN retail_val.tier1_retail_temp + po.tier1_extra_retail else retail_val.tier1_retail_temp end as tier1_retail_temp,
					case when po.tier2_extra_retail > 0 THEN retail_val.tier2_retail + po.tier2_extra_retail else retail_val.tier2_retail end as tier2_retail,
					case when po.less_than_40_extra_retail > 0 THEN retail_val.less_than_40_retail + po.less_than_40_extra_retail else retail_val.less_than_40_retail end as less_than_40_retail

                    from purchase_order as po 
                    left join res_partner rp on po.partner_id = rp.id
                    left join res_users rus on po.acq_user_id = rus.id
				    left join account_payment_term apt on apt.id = po.payment_term_id
                    left join  (select rps1.name,res1.id from res_users  res1 join res_partner rps1 
                    on res1.partner_id = rps1.id ) 
                    as acq_man   on  acq_man.id = po.acq_user_id
					left join (select order_id,sum(product_unit_price * product_qty) as total_retail,
					sum(product_offer_price*product_qty) as total_offer,
					sum(product_unit_price * qty_invoiced) as billed_retail,sum(product_offer_price*qty_invoiced) as billed_offer
					from purchase_order_line   group by  order_id  ) as amount on amount.order_id = po.id


                    left join (
                    select distinct pol.order_id ,sp.date_done from stock_move  sm left join purchase_order_line pol on pol.id = sm.purchase_line_id 
                                    left join stock_picking sp on sp.id=sm.picking_id
                                     where pol.order_id is not null and sp.state='done'
                    ) as date_done on date_done.order_id = po.id

                    left join(		

                    select  pof1.id as order_id,

                    sum(case when (   ( (rpf1.is_wholesaler != true  or rpf1.is_wholesaler is null ) and ttf1.code='1' )

                       or
                         ((rpf1.is_wholesaler = true) and ttf1.code='1' and polf1.product_unit_price!=0 and
                     (ABS(cast((polf1.product_offer_price/polf1.product_unit_price)-1 as numeric)) >= 0.48 )) )
                    then (polf1.product_unit_price * polf1.qty_invoiced) else 0 end ) as tier1_retail_temp ,

                        sum(case when  ( (rpf1.is_wholesaler != true  or rpf1.is_wholesaler is null ) and ttf1.code='2') 
                        
                        or
                         ( (rpf1.is_wholesaler = true) and (((ttf1.code='1' and polf1.product_unit_price!=0 and 
                        (ABS(cast((polf1.product_offer_price/polf1.product_unit_price)-1 as numeric))  >= 0.4 )) 
                        and (ABS(cast((polf1.product_offer_price/polf1.product_unit_price)-1 as numeric)) < 0.48 )) 
                        or (ttf1.code='2' and polf1.product_unit_price!=0 and (ABS(cast((polf1.product_offer_price/polf1.product_unit_price)-1 as numeric))  >= 0.4) )))
                    then (polf1.product_unit_price * polf1.qty_invoiced) else 0 end ) as tier2_retail ,

                    sum(case when  (rpf1.is_wholesaler = true) and ( polf1.product_unit_price!=0 and 
                    (ABS(cast((polf1.product_offer_price/polf1.product_unit_price) -1 as numeric)) < 0.4 )) 
                    then (polf1.product_unit_price * polf1.qty_invoiced) else 0 end ) as less_than_40_retail 

                    from purchase_order pof1 left join purchase_order_line polf1 on pof1.id = polf1.order_id
                    left join product_product ppf1 on ppf1.id =polf1.product_id
                        left join product_template ptf1 on ptf1.id = ppf1.product_tmpl_id
                        left join tier_tier ttf1 on ptf1.tier=ttf1.id 
                        left join res_partner rpf1 on pof1.partner_id = rpf1.id
                        where  pof1.vendor_offer_data =true
                        group by pof1.id
                  ) as retail_val  on retail_val.order_id = po.id

                   where(po.state in ('purchase', 'cancel', 'ven_draft', 'ven_sent','done') and
                   po.status in ('purchase', 'cancel', 'ven_draft', 'ven_sent','done')) 
                   order by po.name desc

                """
        # where(po.state in ('purchase', 'cancel', 'ven_draft', 'ven_sent') and
        #       po.status in ('purchase', 'cancel', 'ven_draft', 'ven_sent'))
        # or po.vendor_offer_data = true
        request.env.cr.execute(str_functions)
        order_lines = request.env.cr.dictfetchall()

        records = []

        for line in order_lines:
            records.append([line['appraisal_no'], line['acq_manager'], line['facility'], line['vendor_cust_id'],
                            line['ap_type'], line['po'],
                            line['payment_term'], line['total_offer'], line['total_retail'], line['billed_offer'],
                            line['final_billed_offer_total'], line['billed_retail'], line['final_billed_retail_total'],
                            line['create_date'],

                            line['shipping_label_issued'], line['shipping_date'], line['delivered_date'],
                            line['arrival_date_grp'], line['tier1_retail_temp'], line['tier2_retail'],
                            line['less_than_40_retail'],
                            line['new_customer'], line['status']])

        res = request.make_response(
            self.from_data(["Appraisal No", "Acq Manager", "Facility","Customer ID", "Type", "PO#", "Payment Term",
                            "Total Offer", "Total Retail", "Billed Total Offer", "Final Billed Total Offer",
                            "Billed Total Retail", "Final Billed Total Retail", "Created On",
                            "Shipping label Issued", "Shipping Date",
                            "Delivered Date", "Arrival Date", "Tier 1 Retail", "Tier 2 Retail", "< 40% Retail",
                            "New Customer", "Status"],
                           records),
            headers=[('Content-Disposition', content_disposition('appraisal_tracker' + '.xls')),
                     ('Content-Type', 'application/vnd.ms-excel')],
        )

        return res
