from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.osv import expression
import datetime
import logging

_logger = logging.getLogger(__name__)


class ProductionLot(models.Model):
    _inherit = 'stock.lot'
    _name = 'stock.lot'
    _description = "ProductionLot"

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

    available_qty_for_sale = fields.Float(compute='_compute_available_qty', store=False, readonly=True, search='_search_available_qty_for_sale')

    def _compute_available_qty(self):
        for lot in self:
            pick_id = self.env.context.get('active_picking_id')
            stock_move = self.env['stock.move'].search([('picking_id', '=', pick_id)], limit=1)
            aval_qty = self.env['stock.quant']._get_available_quantity(lot.product_id, stock_move.location_id,
                                                                       lot_id=lot, package_id=None,
                                                                       owner_id=None, strict=False,
                                                                       allow_negative=False)
            lot.available_qty_for_sale = aval_qty

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
        _logger.info("check_barcode_date stock prod lot create")
        if 'use_date' not in vals:
            vals = self._set_required_vals_to_create_lot(vals)
            # raise UserError(_('Lot expiration date is required.'))
        elif ( ('use_date' in vals and 'alert_date' in vals and vals['alert_date']!=False) and
               (fields.Datetime.from_string(vals['alert_date']) >= fields.Datetime.from_string(vals['use_date']))):
            temp_date = fields.Datetime.from_string(vals['use_date']) - datetime.timedelta(days=3)
            alert_date = temp_date.strftime('%Y-%m-%d %H:%M:%S')
            vals['alert_date'] = alert_date
            # raise UserError(_('Alert date should be less than expiration date.'))
        dates = self._get_dates(vals.get('product_id') or self.env.context.get('default_product_id'))
        for d in dates:
            if not vals.get(d):
                vals[d] = dates[d]
        return super(ProductionLot, self).create(vals)

    def _set_required_vals_to_create_lot(self, vals):
        _logger.info("check_barcode_date stock prod lot set_required_vals_to_create_lot")
        if 'expiration_date' not in vals:
            vals.update({'use_date': fields.Datetime.add(fields.Datetime.now(), years=50), 'alert_date': False,
                         'expiration_date': fields.Datetime.add(fields.Datetime.now(), years=50),
                         'removal_date': False})
            _logger.info("check_barcode_date stock prod lot set_required_vals_to_create_lot 1")
        else:
            if vals['expiration_date'] is not False:
                _logger.info("check_barcode_date stock prod lot set_required_vals_to_create_lot 3")
                _logger.info(vals['expiration_date'])
                temp_date = fields.Datetime.from_string(vals['expiration_date']) - datetime.timedelta(days=3)
                str_date = temp_date.strftime('%Y-%m-%d %H:%M:%S')
                vals.update({'use_date': vals['expiration_date'], 'alert_date': str_date,
                             'expiration_date': vals['expiration_date'],
                             'removal_date': vals['expiration_date']})
                _logger.info("check_barcode_date stock prod lot set_required_vals_to_create_lot 3 done")
            else:
                vals.update({'use_date': vals['expiration_date'], 'alert_date': False,
                             'expiration_date': vals['expiration_date'], 'removal_date': False})
            _logger.info("check_barcode_date stock prod lot set_required_vals_to_create_lot 2")
        return vals

    def write(self, vals):
        _logger.info("check_barcode_date stock prod lot  write")
        if 'use_date' in vals and 'alert_date' in vals:
            if fields.Datetime.from_string(vals['alert_date']) >= fields.Datetime.from_string(vals['use_date']):
                _logger.info("stock lot::write()::-> alert date is greater than use date")
                alter_date = fields.Datetime.from_string(vals['use_date']) - datetime.timedelta(days=3)
                vals['alert_date'] = alter_date.strftime('%Y-%m-%d %H:%M:%S')
                # raise UserError(_('Alert date should be less than expiration date.'))
                _logger.info("stock lot::write()::-> alert date assigned less than use date")
            _logger.info("check_barcode_date stock prod lot  write 1")
        if 'use_date' not in vals and 'alert_date' in vals:
            _logger.info("stock lot::write()::-> use date not specified but alert date specified  %s ,  %s",vals['use_date'], vals['alert_date'])
            if vals['alert_date'] is not False:
                if fields.Datetime.from_string(vals['alert_date']) >= fields.Datetime.from_string(self.use_date):
                    use_date = fields.Datetime.from_string(vals['alert_date']) + datetime.timedelta(days=3)
                    vals['use_date'] = use_date.strftime('%Y-%m-%d %H:%M:%S')
                    _logger.info("stock lot::write()::-> use date not specified but alert date specified "
                                 "and alert date is greater than used date")
                    # raise UserError(_('Alert date should be less than expiration date.'))
                _logger.info("check_barcode_date stock prod lot  write 2")
            _logger.info("check_barcode_date stock prod lot  write 3")
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
        return []

    def _search_qty_available_new(self, operator, value):
        # lot_list = self.env['stock.production.lot'].search([('product_id','=',self._context['default_product_id']),('product_qty','>', value)]).ids
        lot_list = [0]
        for lot in list(filter(lambda x: (x.product_qty > value), self.env['stock.lot'].search([('product_id','=',self._context['default_product_id'])]))):
            lot_list.append(lot.id)
        return lot_list

    def _search_available_qty_for_sale(self, operator, value):
        comparison_functions = {
            '>': lambda x, y: x > y,
            '<': lambda x, y: x < y,
            '>=': lambda x, y: x >= y,
            '<=': lambda x, y: x <= y,
            '=': lambda x, y: x == y,
            '!=': lambda x, y: x != y
        }
        comparison_function = comparison_functions.get(operator)
        if comparison_function:
            record = self.search([('product_id','=',self._context['default_product_id'])], limit=None)
            filtered_ids = [a.id for a in record if comparison_function(a.available_qty_for_sale, value)]
            return [('id', 'in', filtered_ids)]
        else:
            return expression.FALSE_DOMAIN