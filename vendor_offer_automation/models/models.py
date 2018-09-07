# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class vendor_offer_automation(models.Model):
    _description = "Vendor Offer Automation"
    _inherit = "purchase.order"

    template_name = fields.Char(compute="_value_pc", store=True, reqiured=True)
    document = fields.Binary()
    filename = fields.Char(string='File')
    template_exists = fields.Boolean(default=False)

    @api.multi
    @api.depends('partner_id')
    def _value_pc(self):
       self.update_template_name()

    @api.multi
    @api.onchange('partner_id')
    def on_partner_changed(self):
        self.update_template_name()

    @api.model
    def create(self, vals):
        record = super(vendor_offer_automation, self).create(vals)
        record.map_customer_sku_with_catelog_number()
        return record

    @api.model
    def map_customer_sku_with_catelog_number(self):
        # _logger.info('%r', self)

        pass


    @api.multi
    def write(self, vals):
        res = super(vendor_offer_automation, self).write(vals)
        return res

    def update_template_name(self):
        for order in self:
            vendor_offer_templates = order.env['sps.vendor_offer_automation.template'].search(
                [('customer_id', '=', order.partner_id.id), ('template_status', '=', 'Active')])
            if len(vendor_offer_templates) > 0:
                order.template_name = vendor_offer_templates[0].file_name
                order.template_exists = True
                _logger.info('order.template_name %r %r', order.partner_id.id, order.template_name)
            else:
                order.template_exists = False

