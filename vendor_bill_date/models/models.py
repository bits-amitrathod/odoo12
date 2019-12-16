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
                self.date_invoice = str(max_po_id.date_done)

    @api.model
    def create(self, vals):
        ret_invoice=super(VendorBillDate,self).create(vals)
        ret_invoice.action_date_assign()
        return ret_invoice


class Memo(models.Model):
    _inherit = "account.payment"