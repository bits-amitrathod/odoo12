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

    #@api.multi
    def addObject(self, filtered_by_current_month):
        dict = {}
        log.info(" inside addObject ")
        for record in filtered_by_current_month:
            object = Discount()
            object.sale_order = record.name
            object.customer = record.partner_id.name
            if record.confirmation_date:
                object.confirmation_date = datetime.datetime.strptime(str(record.confirmation_date),
                                                                      "%Y-%m-%d %H:%M:%S").date().strftime('%m/%d/%Y')
            else:
                object.confirmation_date = record.confirmation_date
            sum = 0
            for r1 in record.order_line:
                sum = sum + (r1.product_uom_qty * r1.price_unit)

            object.amount = record.amount_untaxed
            object.discount_amount = float(sum - record.amount_untaxed)
            object.total_amount = record.amount_total
            dict[record.id] = object

        log.info(" return addObject ")
        return dict


class ReportBrokerReport(models.AbstractModel):
    _name = 'report.broker_report.brokerreport_temp_test'
    _description = "Report Broker Report"

    @api.model
    def _get_report_values(self, docids, data):

        apprisal_list = {}
        if ('start_date' in data and 'end_date' in data and data['start_date'] != False and data['end_date'] != False):
            apprisal_list = self.env['purchase.order'].with_context(vendor_offer_data=True).search(
                [('state', '=', 'purchase'), ('status', '=', 'purchase'), ('vendor_offer_data', '=', True),
                 ('date_order', '>=', data['start_date']), ('date_order', '<=', data['end_date'])])
            s_date = data['start_date']  # .replace("-", "/")
            e_date = data['end_date']  # .replace("-", "/")
        else:
            apprisal_list = self.env['purchase.order'].with_context(vendor_offer_data=True).search(
                [('state', '=', 'purchase'), ('status', '=', 'purchase'), ('vendor_offer_data', '=', True)])
            s_date = False
            e_date = False
        log.info(apprisal_list)
        if (len(apprisal_list) > 0):
            apprisal_list_rtl_val = apprisal_list_tot_val = apprisal_list_mar_val = apprisal_list[0]
            apprisal_list_report = []
            tot_offer = 0
            margin40tot = 0

            margin_retailamount = 0
            margin_offeramount = 0

            t1t2_margin_retailamount = 0
            tit2_margin_offeramount = 0

            m40_margin_retailamount = 0
            m40_margin_offeramount = 0

            for order in apprisal_list:

                total_retail_broker = str(
                    float(apprisal_list_rtl_val.total_retail_broker) + float(order.rt_price_total_amt))
                bonus_eligible_loop = apprisal_list_rtl_val.bonus_eligible + order.bonus_eligible
                hospital_total_loop = apprisal_list_rtl_val.hospital_total + order.hospital_total
                broker_total_loop = apprisal_list_rtl_val.broker_total + order.broker_total
                broker_greater_40_total_loop = apprisal_list_rtl_val.broker_greater_40_total + order.broker_greater_40_total
                broker_less_40_total_loop = apprisal_list_rtl_val.broker_less_40_total + order.broker_less_40_total
                broker_desc = "RETAIL $ VALUE"

                apprisal_list_rtl_val.update({
                    'total_retail_broker': total_retail_broker,
                    'bonus_eligible': bonus_eligible_loop,
                    'broker_total': broker_total_loop,
                    'broker_greater_40_total': broker_greater_40_total_loop,
                    'broker_less_40_total': broker_less_40_total_loop,
                    'broker_desc': broker_desc,
                    'hospital_total': hospital_total_loop
                })

                tot_offer = tot_offer + order.amount_total

                if order.rt_price_total_amt != 0:

                    if (str(order.broker_margin) == "Margin < 40%") or (str(order.broker_margin) == "T1 BROKER") or (str(order.broker_margin) == "T2 BROKER"):
                        margin_retailamount = margin_retailamount + order.rt_price_total_amt
                        margin_offeramount = margin_offeramount + order.amount_total

                    if (str(order.broker_margin) == "T1 BROKER") or (str(order.broker_margin) == "T2 BROKER"):
                        t1t2_margin_retailamount = t1t2_margin_retailamount + order.rt_price_total_amt
                        tit2_margin_offeramount = tit2_margin_offeramount + order.amount_total

                    if (str(order.broker_margin) == "Margin < 40%"):
                        m40_margin_retailamount = m40_margin_retailamount + order.rt_price_total_amt
                        m40_margin_offeramount = m40_margin_offeramount + order.amount_total

                    if (order.broker_margin == "Margin < 40%"):
                        margin40tot = float(margin40tot) + order.rt_price_total_amt

            bonus_eligible = apprisal_list_rtl_val.total_retail_broker - margin40tot
            eligible_offer = tot_offer - m40_margin_offeramount
            hospital_total = float(apprisal_list_rtl_val.total_retail_broker) - float(
                margin_retailamount)
            broker_total = margin_retailamount
            broker_greater_40_total = t1t2_margin_retailamount
            broker_less_40_total = m40_margin_retailamount

            apprisal_list_rtl_val.update({
                'bonus_eligible': bonus_eligible,
                'hospital_total': hospital_total,
                'broker_total': broker_total,
                'broker_greater_40_total': broker_greater_40_total,
                'broker_less_40_total': broker_less_40_total
            })

            if apprisal_list_rtl_val.total_retail_broker == 0:
                total_retail_broker_tot = 0
                bonus_eligible_tot = 0
                hospital_total_tot = 0
                broker_total_tot = 0
                broker_greater_40_total_tot = 0
                broker_less_40_total_tot = 0
            else:
                total_retail_broker_tot = round(
                    float(apprisal_list_rtl_val.total_retail_broker / apprisal_list_rtl_val.total_retail_broker) * 100,
                    2)
                bonus_eligible_tot = round(
                    (apprisal_list_rtl_val.bonus_eligible / apprisal_list_rtl_val.total_retail_broker) * 100, 2)

                hospital_total_tot = round((float(apprisal_list_tot_val.hospital_total) / float(
                    apprisal_list_rtl_val.total_retail_broker)) * 100, 2)
                broker_total_tot = round(
                    float(apprisal_list_tot_val.broker_total) / float(apprisal_list_rtl_val.total_retail_broker) * 100,
                    2)
                broker_greater_40_total_tot = round(float(apprisal_list_rtl_val.broker_greater_40_total) / float(
                    apprisal_list_rtl_val.total_retail_broker) * 100, 2)
                broker_less_40_total_tot = round(float(apprisal_list_rtl_val.broker_less_40_total) / float(
                    apprisal_list_rtl_val.total_retail_broker) * 100, 2)

            apprisal_list_tot_val.update({
                'total_retail_broker_tot': total_retail_broker_tot,
                'bonus_eligible_tot': bonus_eligible_tot,
                'hospital_total_tot': hospital_total_tot,
                'broker_total_tot': broker_total_tot,
                'broker_greater_40_total_tot': broker_greater_40_total_tot,
                'broker_less_40_total_tot': broker_less_40_total_tot
            })

            if (apprisal_list_rtl_val.total_retail_broker != 0):
                apprisal_list_mar_val.total_retail_broker_mar = str(
                    abs(round((1 - (tot_offer / apprisal_list_rtl_val.total_retail_broker)) * 100, 2))) + ' %'

            else:
                apprisal_list_mar_val.total_retail_broker_mar = "0 %"

            if apprisal_list_rtl_val.bonus_eligible != 0:
                apprisal_list_mar_val.bonus_eligible_mar = str(
                    round(abs((1 - ((float(eligible_offer)) / float(apprisal_list_tot_val.bonus_eligible)))) * 100,
                          2)) + ' %'

            else:
                apprisal_list_mar_val.bonus_eligible_mar = "0 %"

            if apprisal_list_rtl_val.total_retail_broker - margin_retailamount != 0:
                apprisal_list_mar_val.hospital_total_mar = str(abs(round(1 - (float(
                    tot_offer - margin_offeramount)) / (
                                                                                     apprisal_list_rtl_val.total_retail_broker - margin_retailamount),
                                                                         2))) + ' %'
            else:
                apprisal_list_mar_val.hospital_total_mar = '0 %'

            if margin_retailamount != 0:
                apprisal_list_mar_val.broker_total_mar = str(
                    abs(abs(round(1 - float(margin_offeramount) / margin_retailamount, 2)))) + "%"
            else:
                apprisal_list_mar_val.broker_total_mar = "0 %"

            if (t1t2_margin_retailamount != 0):
                apprisal_list_mar_val.broker_greater_40_total_mar = str(
                    abs(round(1 - (float(tit2_margin_offeramount) / float(t1t2_margin_retailamount)), 2))) + "%"
            else:
                apprisal_list_mar_val.broker_greater_40_total_mar = "0 %"

            if (m40_margin_retailamount != 0):
                apprisal_list_mar_val.broker_less_40_total_mar = str(
                    abs(round(1 - (float(m40_margin_offeramount) / float(m40_margin_retailamount)), 2))) + "%"
            else:
                apprisal_list_mar_val.broker_less_40_total_mar = "0 %"

            apprisal_list_tot_val.update({
                'broker_desc_mar': "MARGIN %",
                'broker_desc_tot': "% OF TOTAL"
            })

            apprisal_list_report.append(apprisal_list_rtl_val)
            apprisal_list_report.append(apprisal_list_tot_val)
            apprisal_list_report.append(apprisal_list_mar_val)

            return {'data': apprisal_list_report, 'e_date': e_date, 's_date': s_date}
        else:
            return {'data': apprisal_list, 'e_date': e_date, 's_date': s_date}
