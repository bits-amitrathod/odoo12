# -*- coding: utf-8 -*-

from odoo import models, fields, api

class VendorBillDate(models.Model):
    _inherit ='account.invoice'

    @api.onchange('payment_term_id', 'date_invoice')
    def _onchange_payment_term_date_invoice(self):
        super(VendorBillDate,self). _onchange_payment_term_date_invoice()
        stock_picking_obj = False

        if self.type == "in_invoice" and self.origin :
            # Populates Bill_Date on pageload (onchange()) at the time of creating bill of purchase_order in Purchase module
            stock_picking_obj = self.env['stock.picking'].search([('origin', '=', self.origin),('state','=','done')])

        elif self.type == "out_invoice" and self.origin :
            # Populates Invoice_Date on pageload (onchange()) at the time of creating invoice of sale_order in Sale module
            stock_picking_obj= self.env['stock.picking'].search([('origin', '=', self.origin),('state','=','done'),('picking_type_id','=',5)])

        if stock_picking_obj:
            max_po_id = max(stock_picking_obj)
            self.date_invoice = str(max_po_id.date_done)

        if self.payment_term_id:
            pterm = self.payment_term_id
            pterm_list = pterm.with_context(currency_id=self.company_id.currency_id.id).compute(value=1, date_ref=self.date_invoice)[0]
            self.date_due = max(line[0] for line in pterm_list)
        elif self.date_due and (self.date_invoice > self.date_due):
            self.date_due = self.date_invoice


    # Populates Due_Date at the time of Saving bill of purchase order in Purchase module when click on 'Save' button
    @api.model
    def create(self, vals):
        ret_invoice=super(VendorBillDate,self).create(vals)
        ret_invoice.action_date_assign()
        return ret_invoice


class Memo(models.Model):
    # Via this inherited model handled an xml condition
    _inherit = "account.payment"