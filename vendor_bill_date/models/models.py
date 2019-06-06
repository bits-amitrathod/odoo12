# -*- coding: utf-8 -*-

from odoo import models, fields, api

class VendorBillDate(models.Model):
    _inherit ='account.invoice'

    @api.onchange('payment_term_id', 'date_invoice')
    def _onchange_payment_term_date_invoice(self):
        super(VendorBillDate,self). _onchange_payment_term_date_invoice()

        if self.type == "in_invoice" and self.origin :
            stock_picking_obj = self.env['stock.picking'].search([('origin', '=', self.origin),('state','=','done')])
            if stock_picking_obj:
                max_po_id=max(stock_picking_obj)
                self.date_invoice = max_po_id.date_done

class Memo(models.Model):
    _inherit = "account.payment"
