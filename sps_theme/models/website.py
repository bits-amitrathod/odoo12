# -*- coding: utf-8 -*-
from typing import Dict, Any

from odoo import models, fields, api
from odoo.tools.translate import _
import logging
# from odoo.addons.http_routing.models.ir_http import slugify, _guess_mimetype
_logger = logging.getLogger(__name__)

class Website(models.Model):
    _inherit = "website"

    @staticmethod
    def _get_product_sort_mapping():
        return [
            ('website_sequence asc', _('Featured')),
            ('create_date desc', _('Newest Arrivals')),
            ('actual_quantity asc', _('Quantity: Low to High')),
            ('actual_quantity desc', _('Quantity: High to Low')),
            ('name asc', _('Name - A to Z')),
            ('name desc', _('Name - Z to A')),
            ('list_price asc', _('Catalog Price: Low to High')),
            ('list_price desc', _('Catalog Price: High to Low')),
        ]
