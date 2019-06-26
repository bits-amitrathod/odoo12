
from odoo import models, fields, api, _


class VendorBillPartnerName(models.Model):
    _inherit = "res.partner"

    type = fields.Selection(
        [('contact', 'Contact'),
         ('invoice', 'Invoice address'),
         ('delivery', 'Shipping address'),
         # ('other', 'Other address'),
         # ('private', 'Private Address'),
         ('ap', 'AP Address'),
         ], string='Address Type',
        default='contact',
        help="Used to select automatically the right address according to the context in sales and purchases documents.")

    @api.multi
    def name_get(self):

        res = []
        for partner in self:
            name = partner.name or ''
            if (self.env.context.get('vendor_bill_partner_name_display_name') and True != ('show_address' in self._context)) or\
                    (self.env.context.get('vendor_payment_partner_name_display_name') and True != ('show_address' in self._context)) or\
                    (self.env.context.get('sale_order_invice_name_display_name') and True != ('show_address' in self._context)) or\
                    (self.env.context.get('sale_order_delivery_name_display_name') and True != ('show_address' in self._context))  :
                if partner.company_name or partner.parent_id:
                    if not name and partner.type in ['invoice', 'delivery', 'other','ap']:
                        name = dict(self.fields_get(['type'])['type']['selection'])[partner.type]
                    if not partner.is_company:
                        name = "%s :- %s ,%s" % ((partner.type).upper(),
                                                partner.commercial_company_name or partner.parent_id.name,name)
                else:
                    name = "%s :- %s" % ((partner.type).upper(),
                                          partner.commercial_company_name or partner.name)
            else:
                if partner.company_name or partner.parent_id:
                    if not name and partner.type in ['invoice', 'delivery', 'other','ap']:
                        name = dict(self.fields_get(['type'])['type']['selection'])[partner.type]
                    if not partner.is_company:
                        name = "%s ,%s" % (partner.commercial_company_name or partner.parent_id.name,name)

            if self._context.get('show_address_only'):
                name = partner._display_address(without_company=True)
            if self._context.get('show_address'):
                name = name + "\n" + partner._display_address(without_company=True)
            name = name.replace('\n\n', '\n')
            name = name.replace('\n\n', '\n')
            if self._context.get('show_email') and partner.email:
                name = "%s <%s>" % (name, partner.email)
            if self._context.get('html_format'):
                name = name.replace('\n', '<br/>')
            res.append((partner.id, name))
        return res

