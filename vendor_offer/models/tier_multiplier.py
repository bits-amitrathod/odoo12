from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp


class Multiplier(models.Model):
    _name = 'multiplier.multiplier'
    _description = "Multiplier"

    name = fields.Char(string="Multiplier Name", required=True)
    code = fields.Char(string="Multiplier Code", required=True)
    retail = fields.Float('Retail %', digits=dp.get_precision('Product Unit of Measure'), required=True)
    margin = fields.Float('Margin %', digits=dp.get_precision('Product Unit of Measure'), required=True)


class Competition(models.Model):
    _name = 'competition.competition'
    _description = "Competition"

    name = fields.Char(string="Competition Name", required=True)
    margin = fields.Float('Margin %', digits=dp.get_precision('Product Unit of Measure'), required=True)


class Tier(models.Model):
    _name = 'tier.tier'
    _description = "Product Tier"

    name = fields.Char(string="Product Tier", required=True)
    code = fields.Char(string="Product Tier Code", required=True)


class ClassCode(models.Model):
    _name = 'classcode.classcode'
    _description = "Class Code"

    name = fields.Char(string="Class Code", required=True)


class ProductTemplateTire(models.Model):
    _inherit = 'product.template'

    tier = fields.Many2one('tier.tier', string="Tier")
    class_code = fields.Many2one('classcode.classcode', string="Class Code")
    actual_quantity = fields.Float('Qty Available For Sale', compute="_compute_qty_available", search='_search_qty_available', compute_sudo=False, digits='Product Unit of Measure', store=True)

    @api.depends('product_variant_ids', 'product_variant_ids.stock_quant_ids',
                 'product_variant_ids.stock_quant_ids.reserved_quantity',
                 'product_variant_ids.stock_move_ids.product_qty', 'product_variant_ids.stock_move_ids.state')
    @api.depends_context('product_id', 'company', 'location', 'warehouse')
    def _compute_qty_available(self):
        for template in self:
            stock_quant = self.env['stock.quant'].search([('product_tmpl_id', '=', template.id)])
            reserved_quantity = 0
            if len(stock_quant) > 0:
                for lot in stock_quant:
                    reserved_quantity += lot.reserved_quantity

            template.update({'actual_quantity': template.qty_available - reserved_quantity})
            # print("---------------template -------------------------")
            # print(template)
            # print(template.actual_quantity)

    @api.model
    def create(self, vals):

        if 'tier' in vals and not vals['tier']:
            vals['tier'] = 2

        return super(ProductTemplateTire, self).create(vals)

# ------------------ NOTE ACTIVITY -----------------


class ProductNotesActivity(models.Model):
    _name = 'purchase.notes.activity'
    _description = "Purchase Notes Activity"
    _order = 'id desc'

    order_id = fields.Many2one('purchase.order', string='Order Reference', index=True, required=True,
                               ondelete='cascade')
    note = fields.Text(string="Note", required=True)
    note_date = fields.Datetime(string="Note Date", default=fields.Datetime.now, )

    def action_add_note(self):
        self.write({'note': self.note})