from odoo import api, fields, models


class accoun_invoicr_changes(models.Model):
    _inherit = "account.invoice"

    pay_to = fields.Char("Payable To ", compute="_compute_data")
    address = fields.Char("Full Address ", compute="_compute_data")
    acquisition_rep = fields.Char("Acquisition Rep ", compute="_compute_data")
    company_name = fields.Char("Vendor Name ", compute="_compute_data")

    def _compute_data(self):
        for sp in self:
            inv_cntact = None;
            address = None;
            if sp.partner_id:
                sp.company_name = sp.partner_id.commercial_company_name
                inv_cntact = sp.partner_id

            if inv_cntact is not None :
                sp.pay_to = inv_cntact.name if inv_cntact.name is not None else ""
                if inv_cntact.street: address = inv_cntact.street
                if inv_cntact.street2: address = (address + ', ' + inv_cntact.street2 if  address is not None else inv_cntact.street2)
                if inv_cntact.city: address = (address + ', ' + inv_cntact.city if  address is not None else inv_cntact.city )
                if inv_cntact.state_id and inv_cntact.state_id.name : address = (address + ', ' + inv_cntact.state_id.name if  address is not None else  inv_cntact.state_id.name)
                if inv_cntact.zip: address = (address + ', ' + inv_cntact.zip if  address is not None else  inv_cntact.zip )
                if inv_cntact.country_id   and inv_cntact.country_id.name : address = (address + ', ' + inv_cntact.country_id.name if address is not None else inv_cntact.country_id.name )
            if address is not None: sp.address = address
            purchase_order = self.env["purchase.order"].search([('name', '=', sp.origin)])
            if purchase_order and purchase_order.acq_user_id and purchase_order.acq_user_id.partner_id and purchase_order.acq_user_id.partner_id.name :
                sp.acquisition_rep = purchase_order.acq_user_id.partner_id.name
