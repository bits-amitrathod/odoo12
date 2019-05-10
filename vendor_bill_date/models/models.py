# -*- coding: utf-8 -*-

from odoo import models, fields, api

class VendorBillDate(models.Model):
    _inherit ='account.invoice'

    @api.onchange('payment_term_id', 'date_invoice')
    def _onchange_payment_term_date_invoice(self):
        super(VendorBillDate,self). _onchange_payment_term_date_invoice()

        if self.type == "in_invoice" and self.origin :


            stock_picking_obj = self.env['stock.picking'].search([('origin', '=', self.origin),('state','=','done')])
            max_po_id=max(stock_picking_obj)
            print("Type of PO_ID : ",type(max_po_id))
            print("Max of PO_ID : ",max_po_id)

            print("Stock picking OBJ : ",stock_picking_obj)
            print("Stock picking OBJ_2 : ",stock_picking_obj[0])
            print("Stock picking OBJ type : ",type(stock_picking_obj))
            # if len(stock_picking_obj)>1:
                # max_po_id=max(po_id)
                # print("MAX ID DATES : ",max_po_id)

            if stock_picking_obj :
                self.date_invoice = max_po_id.date_done









