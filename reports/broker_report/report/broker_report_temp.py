
import logging
from odoo import api, fields, models
from odoo.tools import float_repr
import datetime

log = logging.getLogger(__name__)


class Discount():
    sale_order = ''
    customer = ''
    confirmation_date = 0
    amount = 0
    discount_amount = 0
    total_amount = 0

    @api.model
    def check(self, data):
        if data:
            return data
        else:
            return " "

    @api.multi
    def addObject(self, filtered_by_current_month):
        dict = {}
        log.info(" inside addObject ")
        for record in filtered_by_current_month:
            object = Discount()
            object.sale_order = record.name
            object.customer = record.partner_id.name
            if record.confirmation_date:
                object.confirmation_date = datetime.datetime.strptime(record.confirmation_date, "%Y-%m-%d %H:%M:%S").date().strftime('%m/%d/%Y')
            else:
                object.confirmation_date = record.confirmation_date
            sum=0
            for r1 in record.order_line:
                sum = sum + (r1.product_uom_qty * r1.price_unit)

            object.amount = record.amount_untaxed
            object.discount_amount = float(sum -record.amount_untaxed)
            object.total_amount = record.amount_total
            dict[record.id] = object

        log.info(" return addObject ")
        return dict


class ReportBrokerReport(models.AbstractModel):
    _name = 'report.broker_report.brokerreport_temp_test'

    @api.model
    def get_report_values(self, docids, data):

         apprisal_list={}
         if(data['start_date']!=False and data['end_date']!=False):
             apprisal_list= self.env['purchase.order'].search([('state', '=', 'purchase'),('status', '=', 'purchase'),('vendor_offer_data', '=', True),('date_order','>=',data['start_date']),('date_order','<=',data['end_date'])])
         else:
             apprisal_list = self.env['purchase.order'].search([('state', '=', 'purchase'), ('status', '=', 'purchase'), ('vendor_offer_data', '=', True) ])
         if(len(apprisal_list)>0):
             apprisal_list_rtl_val = apprisal_list_tot_val = apprisal_list_mar_val = apprisal_list[0]
             apprisal_list_report=[]
             tot_offer=0
             margin40tot=0

             nomargin_retailamount=0
             nomargin_offeramount=0

             margin_retailamount = 0
             margin_offeramount = 0

             t1t2_margin_retailamount = 0
             tit2_margin_offeramount = 0

             m40_margin_retailamount = 0
             m40_margin_offeramount = 0

             for order in apprisal_list:
                 apprisal_list_rtl_val.total_retail_broker = apprisal_list_rtl_val.total_retail_broker + order.retail_amt
                 apprisal_list_rtl_val.bonus_eligible = apprisal_list_rtl_val.bonus_eligible + order.bonus_eligible
                 apprisal_list_rtl_val.hospital_total = apprisal_list_rtl_val.hospital_total + order.hospital_total
                 apprisal_list_rtl_val.broker_total = apprisal_list_rtl_val.broker_total + order.broker_total
                 apprisal_list_rtl_val.broker_greater_40_total = apprisal_list_rtl_val.broker_greater_40_total + order.broker_greater_40_total
                 apprisal_list_rtl_val.broker_less_40_total = apprisal_list_rtl_val.broker_less_40_total + order.broker_less_40_total
                 apprisal_list_rtl_val.broker_desc="RETAIL $ VALUE"
                 tot_offer=tot_offer+order.offer_amount

                 if (order.retail_amt != 0):
                     if((abs(float(((order.offer_amount)/float(order.retail_amt))-1)) < 0.4) or  ( (order.partner_id.is_broker) and (abs(float(order.offer_amount/order.retail_amt)) < 0.52) or (abs(float(order.offer_amount/order.retail_amt)) > 0.52))):
                        margin_retailamount = nomargin_retailamount + order.retail_amt
                        margin_offeramount = nomargin_retailamount + order.offer_amount
                     else:
                        nomargin_retailamount=nomargin_retailamount+ order.retail_amt
                        nomargin_offeramount = nomargin_retailamount + order.offer_amount

                 if (order.retail_amt != 0):
                     if (order.partner_id.is_broker and ((abs(float(order.offer_amount / order.retail_amt)) < 0.52) or (abs(float(order.offer_amount / order.retail_amt)) > 0.52))):
                         t1t2_margin_retailamount = nomargin_retailamount + order.retail_amt
                         tit2_margin_offeramount = nomargin_retailamount + order.offer_amount
                 if (order.retail_amt != 0):
                     if (abs(float(((order.offer_amount) / float(order.retail_amt)) - 1)) < 0.4):
                         m40_margin_retailamount = nomargin_retailamount + order.retail_amt
                         m40_margin_offeramount = nomargin_retailamount + order.offer_amount

                 if (order.retail_amt != 0):
                    if (abs(float(((order.offer_amount) / float(order.retail_amt)) - 1)) < 0.4):
                         margin40tot=float(margin40tot)+order.retail_amt

             apprisal_list_rtl_val.bonus_eligible=apprisal_list_rtl_val.total_retail_broker-margin40tot
             apprisal_list_rtl_val.hospital_total=float(apprisal_list_rtl_val.total_retail_broker) - float(margin_retailamount)
             apprisal_list_rtl_val.broker_total=margin_retailamount
             apprisal_list_rtl_val.broker_greater_40_total = t1t2_margin_retailamount
             apprisal_list_rtl_val.broker_less_40_total = m40_margin_retailamount

             apprisal_list_tot_val.total_retail_broker_tot = round(float(apprisal_list_rtl_val.total_retail_broker/ apprisal_list_rtl_val.total_retail_broker)*100,2)
             apprisal_list_tot_val.bonus_eligible_tot =  round((apprisal_list_rtl_val.bonus_eligible/apprisal_list_rtl_val.total_retail_broker)*100,2)
             apprisal_list_tot_val.hospital_total_tot =round((float(apprisal_list_tot_val.hospital_total_tot)/float(apprisal_list_rtl_val.total_retail_broker))*100,2)
             apprisal_list_tot_val.broker_total_tot =  round(float(apprisal_list_tot_val.broker_total_tot)/float(apprisal_list_rtl_val.total_retail_broker) * 100,2)
             apprisal_list_tot_val.broker_greater_40_total_tot =round(float(apprisal_list_rtl_val.broker_greater_40_total)/float(apprisal_list_rtl_val.total_retail_broker)*100,2)
             apprisal_list_tot_val.broker_less_40_total_tot = round(float(apprisal_list_rtl_val.broker_less_40_total)/float(apprisal_list_rtl_val.total_retail_broker)*100,2)
             apprisal_list_rtl_val.broker_desc_tot = "% OF TOTAL"

             if (apprisal_list_rtl_val.total_retail_broker!= 0):
                apprisal_list_mar_val.total_retail_broker_mar = str(round(abs(((1-float(tot_offer))/float(apprisal_list_rtl_val.total_retail_broker)))*100,2)) + ' %'

             else:
                apprisal_list_mar_val.total_retail_broker_mar="0 %"


             if (apprisal_list_rtl_val.bonus_eligible_tot != 0):
                apprisal_list_mar_val.bonus_eligible_mar = str(round(abs((1-(float(apprisal_list_tot_val.bonus_eligible_tot))/float(apprisal_list_tot_val.bonus_eligible_tot)))*100,2)) + ' %'

             else:
                 apprisal_list_mar_val.bonus_eligible_mar="0 %"

             if(apprisal_list_rtl_val.total_retail_broker-nomargin_retailamount!=0):
                apprisal_list_mar_val.hospital_total_mar = str(round(((1-float(tot_offer-margin_offeramount))/(apprisal_list_rtl_val.total_retail_broker-margin_retailamount)),2) ) + ' %'
             else:
                apprisal_list_mar_val.hospital_total_mar='0 %'


             if(margin_retailamount!=0):
                apprisal_list_mar_val.broker_total_mar =str(abs(round((1-float(margin_offeramount))/margin_retailamount,2))) + "%"
             else:
                apprisal_list_mar_val.broker_total_mar="0 %"



             if(t1t2_margin_retailamount!=0):
                apprisal_list_mar_val.broker_greater_40_total_mar = str(abs(round(((1-float(tit2_margin_offeramount)))/float(t1t2_margin_retailamount),2))) + "%"
             else:
                apprisal_list_mar_val.broker_greater_40_total_mar="0 %"



             if (m40_margin_retailamount != 0):
                apprisal_list_mar_val.broker_less_40_total_mar = str(abs(round((1-float(m40_margin_offeramount))/float(m40_margin_retailamount),2))) + "%"
             else:
                apprisal_list_mar_val.broker_less_40_total_mar="0 %"



             apprisal_list_rtl_val.broker_desc_mar = "MARGIN %"

             apprisal_list_report.append(apprisal_list_rtl_val)
             apprisal_list_report.append(apprisal_list_tot_val)
             apprisal_list_report.append(apprisal_list_mar_val)

             return {'data': apprisal_list_report}
         else:
             return {'data': apprisal_list}