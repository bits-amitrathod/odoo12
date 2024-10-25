from typing import Dict, Any

from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)

class website_product_download_catelog_cstm(models.Model):
    _name = 'sps_theme.product_download_catelog'
    _description = "website_product_download_catelog_cstm"

    file = fields.Binary('File')
    filename = fields.Char()
    status = fields.Selection([('active', 'active'),('inactive', 'Inactive')])

    @api.model
    def create(self, vals):
        self.setActive(vals)
        return super(website_product_download_catelog_cstm, self).create(vals)

    def write(self, vals):
        self.setActive(vals)
        return super(website_product_download_catelog_cstm, self).write(vals)

    def setActive(self,vals):
        if vals.get('status') == 'active':
            self.env.cr.execute(
                "UPDATE sps_theme_product_download_catelog SET  status='inactive' WHERE status ='active'")

