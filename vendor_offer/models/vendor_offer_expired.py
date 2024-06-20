import datetime

from odoo import models, fields, api, _


class VendorOfferExpired(models.Model):
    _description = "Vendor Offer Expiration Date"
    _inherit = "purchase.order"

    offer_expired = fields.Boolean(string='Offer Expired ?')
    offer_approved = fields.Boolean(string='Offer is Approved', track_visibility='onchange')

    def set_expiration_flag_old_offer(self):
        fourteen_days_ago = datetime.datetime.today().date() - datetime.timedelta(days=21)

        expired_offers = self.env['purchase.order'].search([
            ('date_offered', '<', fourteen_days_ago),
            ('offer_expired', '=', False),
            ('state', 'in', ['ven_draft', 'ven_sent']),
        ])

        for offer in expired_offers:
            offer.write({'offer_expired': True, 'offer_approved': False})

    def action_approve_offer(self):
        self.ensure_one()
        self.write({'offer_approved': True})
        return True
