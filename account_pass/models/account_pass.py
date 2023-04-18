from odoo import api, fields, models, _


class account_pass(models.Model):
    _name = "account.pass"
    _description = "Account Pass"

    stage_id = fields.Many2one(
        'account.pass.stage', string='Account pass Stage', index=True,
        readonly=False, store=True, group_expand='_read_group_stage_ids',
        copy=False, ondelete='restrict')

    partner_id = fields.Many2one('res.partner', String='Customer')
    saleforce_ac = fields.Char("SF A/C  No#", compute="partner_depends_value_cal", readonly=False, store=False)

    is_in_stock_report = fields.Boolean(string="In Stock Report")
    in_stock_report_note = fields.Text(string="In Stock Report Note")

    is_follow_up_discussed = fields.Boolean(string="Follow up Cadence Discussed")
    follow_up_discussed_note = fields.Text(string="Follow up Cadence Discussed Note")
    is_req_freq = fields.Boolean(string="Request Frequency")
    req_freq_note = fields.Text(string="Request Frequency Note")
    is_competitor_info = fields.Boolean(string="Competitor Info")
    competitor_info_note = fields.Text(string="Competitor Info Note")
    is_code_in_top_20 = fields.Boolean(string="1 Code in Top 20")
    code_in_top_20_note = fields.Text(string="1 Code in Top 20 Note")

    is_vendors_purchased = fields.Boolean(string="Vendors Purchased")
    vendors_purchased_note = fields.Text(string="Vendors Purchased Note")
    is_unique_codes = fields.Boolean(string="7 Unique Codes")
    unique_codes_note = fields.Text(string="7 Unique Codes Note")
    is_purchase_history = fields.Boolean(string=" Purchase History/ Usage Report")
    purchase_history_note = fields.Text(string=" Purchase History/ Usage Report Note")
    is_average_month = fields.Boolean(string="Average 1 order or more a month")
    average_month_note = fields.Text(string="Average 1 order or more a month Note")
    is_purchased = fields.Boolean(string="Has purchased")
    purchased_note = fields.Text(string="Has purchased Note")
    is_prime_vendor = fields.Boolean(string="Prime Vendor ")
    prime_vendor_note = fields.Text(string="Prime Vendor Note")
    is_integration = fields.Boolean(string="Integration")
    integration_note = fields.Text(string="Integration Note")

    total = fields.Float(string="Total", compute="compute_total")
    backorder = fields.Selection(string='Backorder Only?', selection=[('yes', 'Yes'),('no', 'No')])
    ph = fields.Boolean(string="PH on file?")
    expansion = fields.Boolean(string="Expansion Call Complete?")

    company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.company.id)
    bonused = fields.Boolean(string="Bonused")
    total_account_spend = fields.Monetary(string="Total Account Spend", currency_field='company_currency',)
    company_currency = fields.Many2one("res.currency", string='Currency', related='company_id.currency_id', readonly=True)
    ordering_method = fields.Text(string="Ordering Days/Order Method")
    subspecialties = fields.Text(string="Subspecialties/Manufacturers")
    popular_code = fields.Text(string="Popular Codes they will always buy")
    manufacturers = fields.Text(string="Manufacturers that are off the table?")
    in_stock_report_text = fields.Text(string="In Stock Report up to date w/ all products they can/will buy with us?")
    position = fields.Text(string="Where do they position SPS?")

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        return stages.browse(self.env['account.pass.stage'].search([]).ids)

    @api.onchange('partner_id')
    def partner_depends_value_cal(self):
        for rec in self:
            rec.saleforce_ac = rec.partner_id.saleforce_ac if rec.partner_id else None

    @api.onchange("is_in_stock_report", "is_follow_up_discussed", "is_req_freq", "is_competitor_info", "is_code_in_top_20",
              "is_vendors_purchased", "is_unique_codes", "is_purchase_history", "is_average_month", "is_purchased",
              "is_prime_vendor", "is_integration")
    def compute_total(self):
        for rec in self:
            rec.total = ((0.25 if rec.is_in_stock_report else 0.0) + (0.25 if rec.is_follow_up_discussed else 0.0) + \
                        (0.25 if rec.is_req_freq else 0.0) + (0.25 if rec.is_competitor_info else 0.0) + \
                        (0.25 if rec.is_code_in_top_20 else 0.0) + (0.25 if rec.is_vendors_purchased else 0.0) + \
                        (0.50 if rec.is_unique_codes else 0.0) + (0.50 if rec.is_purchase_history else 0.0) + \
                        (0.75 if rec.is_average_month else 0.0) + (0.75 if rec.is_purchased else 0.0) + \
                        (1.0 if rec.is_prime_vendor else 0.0) + (1.0 if rec.is_integration else 0.0))



