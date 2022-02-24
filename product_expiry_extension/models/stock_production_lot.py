from odoo import api, fields, models, _
from odoo.exceptions import UserError
import datetime
import logging

_logger = logging.getLogger(__name__)


class ProductionLot(models.Model):
    _inherit = 'stock.production.lot'
    _name = 'stock.production.lot'

    expiration_date = fields.Datetime(string='End of Life Date',
                                help='This is the date on which the goods with this Serial Number may become dangerous and must not be consumed.')
    use_date = fields.Datetime(string='Expiration Date',
                               help='This is the date on which the goods with this Serial Number start deteriorating, without being dangerous yet.')
    removal_date = fields.Datetime(string='Removal Date',
                                   help='This is the date on which the goods with this Serial Number should be removed from the stock.')
    alert_date = fields.Datetime(string='Alert Date',
                                 help='Date to determine the expired lots and serial numbers using the filter "Expiration Alerts".')
    product_expiry_alert = fields.Boolean(compute='_compute_product_expiry_alert',
                                          help="The Alert Date has been reached.")
    product_qty = fields.Float('Quantity', compute='_product_qty', search='_search_qty_available')

    @api.depends('expiration_date')
    def _compute_product_expiry_alert(self):
        current_date = fields.Datetime.now()
        for lot in self:
            if lot.expiration_date:
                lot.product_expiry_alert = lot.expiration_date <= current_date
            else:
                lot.product_expiry_alert = False

    def _get_dates(self, product_id=None):
        """Returns dates based on number of days configured in current lot's product."""
        mapped_fields = {
            'expiration_date': 'expiration_time',
            'use_date': 'use_time',
            'removal_date': 'removal_time',
            'alert_date': 'alert_time'
        }
        res = dict.fromkeys(mapped_fields, False)
        product = self.env['product.product'].browse(product_id) or self.product_id
        if product:
            for field in mapped_fields:
                duration = getattr(product, mapped_fields[field])
                if duration:
                    date = datetime.datetime.now() + datetime.timedelta(days=duration)
                    res[field] = fields.Datetime.to_string(date)
        return res

    # Assign dates according to products data
    @api.model
    def create(self, vals):
        if 'use_date' not in vals:
            vals = self._set_required_vals_to_create_lot(vals)
            # raise UserError(_('Lot expiration date is required.'))
        elif ( ('use_date' in vals and 'alert_date' in vals and vals['alert_date']!=False) and
               (fields.Datetime.from_string(vals['alert_date']) >= fields.Datetime.from_string(vals['use_date']))):
            raise UserError(_('Alert date should be less than expiration date.'))
        dates = self._get_dates(vals.get('product_id') or self.env.context.get('default_product_id'))
        for d in dates:
            if not vals.get(d):
                vals[d] = dates[d]
        return super(ProductionLot, self).create(vals)

    def _set_required_vals_to_create_lot(self, vals):
        vals.update({'use_date': fields.Datetime.add(fields.Datetime.now(), years=50), 'alert_date': False, 'expiration_date': fields.Datetime.add(fields.Datetime.now(), years=50), 'removal_date': False})
        return vals

    def write(self, vals):
        if 'use_date' in vals and 'alert_date' in vals:
            if fields.Datetime.from_string(vals['alert_date']) >= fields.Datetime.from_string(vals['use_date']):
                raise UserError(_('Alert date should be less than expiration date.'))
        if 'use_date' not in vals and 'alert_date' in vals:
            if fields.Datetime.from_string(vals['alert_date']) >= fields.Datetime.from_string(self.use_date):
                raise UserError(_('Alert date should be less than expiration date.'))
        if 'product_id' in vals:
            move_lines = self.env['stock.move.line'].search([('lot_id', 'in', self.ids)])
            if move_lines:
                raise UserError(_(
                    'You are not allowed to change the product linked to a serial or lot number ' + 'if some stock moves have already been created with that number. ' + 'This would lead to inconsistencies in your stock.'))
        return super(ProductionLot, self).write(vals)

    @api.onchange('product_id')
    def _onchange_product(self):
        dates_dict = self._get_dates()
        for field, value in dates_dict.items():
            setattr(self, field, value)

    def _search_qty_available(self, operator, value):
        if 'default_product_id' in self._context.keys():
            product_ids = [0]
            if value == 0.0 and operator == '>' and not ({'from_date', 'to_date'} & set(self.env.context.keys())):
                product_ids = self._search_qty_available_new(
                    operator, value )
            return [('id', 'in', product_ids)]
        else:
           pass

    def _search_qty_available_new(self, operator, value):
        # lot_list = self.env['stock.production.lot'].search([('product_id','=',self._context['default_product_id']),('product_qty','>', value)]).ids
        lot_list = [0]
        for lot in list(filter(lambda x: (x.product_qty > value), self.env['stock.production.lot'].search([('product_id','=',self._context['default_product_id'])]))):
             lot_list.append(lot.id)
        return lot_list
