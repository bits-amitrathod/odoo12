# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging
from itertools import groupby
from operator import itemgetter
from odoo.exceptions import ValidationError, AccessError
from odoo.tools.float_utils import float_compare, float_round, float_is_zero
from collections import OrderedDict

_logger = logging.getLogger(__name__)


# Customer Global level setting
class Customer(models.Model):
    _inherit = 'res.partner'

    prioritization = fields.Boolean("Prioritization setting")
    sku_preconfig = fields.Char("SKU PreConfig")
    sku_postconfig = fields.Char("SKU PostConfig")
    prioritization_ids = fields.One2many('prioritization_engine.prioritization', 'customer_id')
    min_threshold = fields.Integer("Product Min Threshold", readonly=False)
    max_threshold = fields.Integer("Product Max Threshold", readonly=False)
    priority = fields.Integer("Product Priority", default=-1, readonly=False,
                              help="If Product Priority is -1 then Prioritization Engine will process only those products which are added in 'Customer Priority Configuration'.")
    cooling_period = fields.Integer("Cooling Period in days", readonly=False)
    auto_allocate = fields.Boolean("Allow Auto Allocation?", readonly=False)
    length_of_hold = fields.Integer("Length Of Hold in hours", readonly=False, default=1)
    doc_process_count = fields.Integer("Document Processing Count", readonly=False, default='1')
    expiration_tolerance = fields.Integer("Expiration Tolerance in Months", readonly=False)
    partial_ordering = fields.Boolean("Allow Partial Ordering?", readonly=False)
    partial_UOM = fields.Boolean("Allow Partial UOM?", readonly=False)
    order_ids = fields.One2many('sale.order', 'partner_id')
    gl_account = fields.One2many('gl.account', 'partner_id', string="GL Account")
    on_hold = fields.Boolean("On Hold")
    is_broker = fields.Boolean("Is a Broker?")
    carrier_info = fields.Char("Carrier Info")
    carrier_acc_no = fields.Char("Carrier Account No")
    quickbook_id = fields.Char("Quickbook Id")
    having_carrier = fields.Boolean("Having Carrier?")
    notification_email = fields.Char("Notification Email")
    saleforce_ac = fields.Char("SF A/C No#", compute="_saleforce_ac_generate",readonly=False, store=True)
    is_share = fields.Boolean("Is Shared")
    sale_margine = fields.Selection([
        ('gifted', 'Gifted'),
        ('legacy', 'Legacy')], string='Sales Level')
    preferred_method = fields.Selection([
        ('mail', 'Mail'),
        ('email', 'E Mail'),
        ('both', 'E Mail & Mail ')], string='Preferred Invoice Delivery Method')
    shipping_terms = fields.Selection([
        ('1', 'Prepaid & Billed'),
        ('2', 'Prepaid'),
        ('3', 'Freight Collect')], string='Shipping Terms')
    allow_purchase = fields.Boolean("Purchase Order Method")
    is_parent = fields.Boolean("Purchase Order Method", default=True)

    @api.onchange('doc_process_count')
    def _onchange_doc_process_count(self):
        if self.doc_process_count < 1:
            raise ValidationError(_('Document Processing Count at least 1'))

    @api.constrains('doc_process_count')
    @api.one
    def _check_doc_process_count(self):
        if self.doc_process_count < 1:
            raise ValidationError(_('Document Processing Count at least 1'))

    @api.model
    def create(self, vals):
        self.copy_parent_date(vals)
        return super(Customer, self).create(vals)

    @api.onchange('saleforce_ac')
    def _saleforce_ac_generate(self):
        for partner in self:
            partner.saleforce_ac = self.env['ir.sequence'].next_by_code('sale.force.no') or _('New')

    @api.multi
    def write(self, vals):
        res = super(Customer, self).write(vals)
        res2 = self.copy_parent_date(vals)
        return res

    def copy_parent_date(self, vals):
        # self.ensure_one()
        _logger.info("pritization engin :%r", vals)
        for ml in self:
            for child_id in ml.child_ids:
                child_id.write({'on_hold': ml.on_hold,
                                'is_broker': ml.is_broker,
                                'carrier_info': ml.carrier_info,
                                'carrier_acc_no': ml.carrier_acc_no,
                                'quickbook_id': ml.quickbook_id,
                                'having_carrier': ml.having_carrier,
                                'preferred_method': ml.preferred_method,
                                'shipping_terms': ml.shipping_terms,
                                'allow_purchase': ml.allow_purchase,
                                'sku_preconfig': ml.sku_preconfig,
                                'sku_postconfig': ml.sku_postconfig,
                                'is_parent': False,
                                'prioritization': ml.prioritization,
                                'prioritization_ids': ml.prioritization_ids,
                                'min_threshold': ml.min_threshold,
                                'priority': ml.priority,
                                'partial_UOM': ml.partial_UOM,
                                'partial_ordering': ml.partial_ordering,
                                'auto_allocate': ml.auto_allocate,
                                'length_of_hold': ml.length_of_hold,
                                'expiration_tolerance': ml.expiration_tolerance,
                                'cooling_period': ml.cooling_period,
                                'max_threshold': ml.max_threshold,
                                'is_share': ml.is_share,
                                'sale_margine': ml.sale_margine
                                })

    def action_view_notification(self):
        '''
        This function returns an action that display existing notification
        of given partner ids. It can be form
        view,
        '''
        action = self.env.ref('prioritization_engine.action_notification_setting').read()[0]
        action['views'] = [(self.env.ref('prioritization_engine.view_notification_setting_form').id, 'form')]
        action['view_ids'] = self.env.ref('prioritization_engine.view_notification_setting_form').id
        action['res_id'] = self.id
        return action

    def action_gl_account(self):
        action = self.env.ref('prioritization_engine.action_glaccount_setting').read()[0]
        action['domain'] = [('partner_id', '=', self.id)]
        action['context'] = {'default_partner_id': self.id}
        return action

    def action_view_import(self):
        '''
        This function returns an action that display existing notification
        of given partner ids. It can be form
        view,
        '''
        action = self.env.ref('stock.product_template_action_product').read()[0]
        action['views'] = [(self.env.ref('product.product_template_tree_view').id, 'tree')]
        action['view_ids'] = self.env.ref('product.product_template_tree_view').id
        action['res_id'] = self.id
        return action

    def action_import_template(self):
        tree_view_id = self.env.ref('customer-requests.view_tree_documents_normal').id
        return {
            'type': 'ir.actions.client',
            'views': [(tree_view_id, 'form')],
            'view_mode': 'form',
            'tag': 'importtemplate',
            'params': [
                {'model': 'sps.customer.template', 'customer_id': self.id, 'user_type': 'customer', 'request_model':
                    'sps.customer.requests'}],
        }

    # constraint
    @api.constrains('expiration_tolerance')
    @api.one
    def _check_expiration_tolerance(self):
        expiration_tolerance = self.expiration_tolerance
        if expiration_tolerance and len(str(abs(expiration_tolerance))) > 3:
            raise ValidationError(
                _('Global Priority Configuration->Expiration Tolerance field must be less than 3 digit'))

    @api.constrains('length_of_hold')
    @api.one
    def _check_length_of_hold(self):
        if self.prioritization:
            length_of_hold = self.length_of_hold
            if length_of_hold and len(str(abs(length_of_hold))) > 5:
                raise ValidationError(
                    _('Global Priority Configuration->Length of Holding field must be less than 5 digit'))
            elif length_of_hold == 0:
                self.length_of_hold = 1
                raise ValidationError(_('Global Priority Configuration->Length of Holding field should not be 0'))

    @api.constrains('priority')
    @api.one
    def _check_priority(self):
        priority = self.priority
        if priority and len(str(abs(priority))) > 5:
            raise ValidationError(_('Global Priority Configuration->Priority field must be less than 5 digit'))

    @api.constrains('cooling_period')
    @api.one
    def _check_cooling_period(self):
        cooling_period = self.cooling_period
        if cooling_period and cooling_period >= 366:
            raise ValidationError(_('Global Priority Configuration->Cooling Period field must be less 365 days'))

    @api.constrains('max_threshold')
    @api.one
    def _check_max_threshold(self):
        max_threshold = self.max_threshold
        if max_threshold and max_threshold >= 999:
            raise ValidationError(_('Global Priority Configuration->Max Threshold field must be less 999'))
        if max_threshold and max_threshold <= self.min_threshold:
            raise ValidationError(
                _('Global Priority Configuration->Max Threshold field must be greater than Min Threshold field'))

    @api.constrains('min_threshold')
    @api.one
    def _check_min_threshold(self):
        min_threshold = self.min_threshold
        if min_threshold and min_threshold > 999:
            raise ValidationError(_('Global Priority Configuration->Min Threshold field must be less 999'))

    @api.onchange('prioritization', 'allow_purchase')
    def _check_prioritization_setting(self):
        warning = {}
        vals = {}
        if self.allow_purchase == False and self.prioritization == True:
            vals.update({'prioritization': False})
            warning = {
                'title': _('Warning'),
                'message': _('Please Select Purchase Order Method For Prioritization setting'),
            }
        return {'value': vals, 'warning': warning}

    @api.multi
    def _check_prioritization_setting_checkbox(self):
        for partner in self:
            if partner.allow_purchase == True and partner.prioritization == True:
                if partner.email and partner.api_secret:
                    base_url = self.env['ir.config_parameter'].get_param('web.base.url')
                    url = base_url+"/api/upload"
                    self.send_mail(url,partner.email, partner.api_secret, partner.id)
                else:
                    raise ValidationError(_(partner.name + ' should have a Username and Password.'))

    def send_mail(self, url, email, password, partner_id):
        template = self.env.ref('prioritization_engine.send_prioritization_credential_email').sudo()
        local_context = {'url': url, 'username': email, 'password': password}
        try:
            template.with_context(local_context).send_mail(partner_id, raise_exception=True, force_send=True, )
        except:
            response = {'message': 'Unable to connect to SMTP Server'}


class ProductTemplateSku(models.Model):
    _inherit = 'product.template'

    def _get_default_uom_id(self):
        return self.env["uom.uom"].search([('name', 'ilike', 'each'),('category_id.id', '=', 1)], limit=1, order='id').id

    location = fields.Char("Location")
    premium = fields.Boolean("Premium")
    sku_code = fields.Char('SKU / Catalog No')
    manufacturer_pref = fields.Char(string='Manuf. Catalog No')
    manufacturer_uom = fields.Many2one('uom.uom', 'Manuf. UOM', default=_get_default_uom_id,
                                       required=True)

    @api.model
    def create(self, vals):
        if 'sku_code' in vals:
            vals['default_code'] = vals['sku_code']
        return super(ProductTemplateSku, self).create(vals)

    @api.multi
    def write(self, vals):
        if 'sku_code' in vals:
            vals['default_code'] = vals['sku_code']
        return super(ProductTemplateSku, self).write(vals)


class NotificationSetting(models.Model):
    _inherit = 'res.partner'

    start_date = fields.Date("Start Date")
    end_date = fields.Date("End Date")
    historic_months = fields.Integer("Last XX Historic Months")
    monday = fields.Boolean("Monday")
    tuesday = fields.Boolean("Tuesday")
    wednesday = fields.Boolean("Wednesday")
    thursday = fields.Boolean("Thursday")
    friday = fields.Boolean("Friday")
    saturday = fields.Boolean("Saturday")
    sunday = fields.Boolean("Sunday")


# Customer product level setting
class Prioritization(models.Model):
    _name = 'prioritization_engine.prioritization'
    _inherits = {'product.product': 'product_id'}
    min_threshold = fields.Integer("Min Threshold", readonly=False)
    max_threshold = fields.Integer("Max Threshold", readonly=False)
    priority = fields.Integer("Product Priority", readonly=False)
    cooling_period = fields.Integer("Cooling Period in days", readonly=False)
    auto_allocate = fields.Boolean("Allow Auto Allocation?", readonly=False)
    length_of_hold = fields.Integer("Length Of Hold in hours", readonly=False, default=1)
    expiration_tolerance = fields.Integer("Expiration Tolerance in months", readonly=False)
    partial_ordering = fields.Boolean("Allow Partial Ordering?", readonly=False)
    partial_UOM = fields.Boolean("Allow Partial UOM?", readonly=False)
    customer_id = fields.Many2one('res.partner', string='GlobalPrioritization', required=True, ondelete="cascade")
    product_id = fields.Many2one('product.product', string='Product', required=True, ondelete="cascade")
    sales_channel = fields.Selection([('1', 'Manual'), ('2', 'Prioritization Engine')], String="Sales Channel",
                                     readonly=False)  # get team id = sales channel like 3 = Manual, 4 = Prioritization Engine

    _sql_constraints = [
        ('priority_engine_uniq', 'unique (product_id,customer_id)',
         'In Customer Priority Configuration Product Value Repeated !')
    ]

    def import_product(self, records, cust_id):
        for record in records:
            self.create({'customer_id': cust_id, 'product_id': record['id']})

    # constraint
    @api.constrains('expiration_tolerance')
    @api.one
    def _check_expiration_tolerance(self):
        expiration_tolerance = self.expiration_tolerance
        if expiration_tolerance and len(str(abs(expiration_tolerance))) > 3:
            raise ValidationError(
                _('Customer Priority Configuration->Expiration Tolerance field must be less than 3 digit'))

    @api.constrains('length_of_hold')
    @api.one
    def _check_length_of_hold(self):
        length_of_hold = self.length_of_hold
        if length_of_hold and len(str(abs(length_of_hold))) > 5:
            raise ValidationError(
                _('Customer Priority Configuration->Length of Holding field must be less than 5 digit'))
        elif length_of_hold == 0:
            raise ValidationError(_('Customer Priority Configuration->Length of Holding field should not be 0'))

    @api.constrains('priority')
    @api.one
    def _check_priority(self):
        priority = self.priority
        if priority and len(str(abs(priority))) > 5:
            raise ValidationError(_('Customer Priority Configuration->Priority field must be less than 5 digit'))

    @api.constrains('cooling_period')
    @api.one
    def _check_cooling_period(self):
        cooling_period = self.cooling_period
        if cooling_period and cooling_period >= 366:
            raise ValidationError(_('Customer Priority Configuration->Cooling Period field must be less 365 days'))

    @api.constrains('max_threshold')
    @api.one
    def _check_max_threshold(self):
        # max_threshold = self.max_threshold
        if self.max_threshold and self.max_threshold >= 999:
            raise ValidationError(_('Customer Priority Configuration->Max Threshold field must be less 999'))
        if self.min_threshold and self.max_threshold <= self.min_threshold:
            raise ValidationError(
                _('Customer Priority Configuration->Max Threshold field must be greater than Min Threshold field'))

    @api.constrains('min_threshold')
    @api.one
    def _check_min_threshold(self):
        min_threshold = self.min_threshold
        if min_threshold and min_threshold > 999:
            raise ValidationError(_('Customer Priority Configuration->Min Threshold field must be less 999'))


class PrioritizationTransient(models.TransientModel):
    _name = 'prioritization.transient'
    min_threshold = fields.Integer("Min Threshold", readonly=False)
    max_threshold = fields.Integer("Max Threshold", readonly=False)
    priority = fields.Integer("Priority")
    cooling_period = fields.Integer("Cooling Period in days")
    auto_allocate = fields.Boolean("Allow Auto Allocation?")
    length_of_hold = fields.Integer("Length Of Hold in hours")
    expiration_tolerance = fields.Integer("Expiration Tolerance in months")
    partial_ordering = fields.Boolean("Allow Partial Ordering?")
    partial_UOM = fields.Boolean("Allow Partial UOM?")

    def action_confirm(self, arg):
        for selected in arg["selected_ids"]:
            record = self.env['prioritization_engine.prioritization'].search([('id', '=', selected)])[0]
            record.write(
                {'min_threshold': self.min_threshold, 'max_threshold': self.max_threshold, 'priority': self.priority,
                 'cooling_period': self.cooling_period, 'auto_allocate': self.auto_allocate,
                 'expiration_tolerance': self.expiration_tolerance, 'partial_ordering': self.partial_ordering,
                 'partial_UOM': self.partial_UOM,
                 'length_of_hold': self.length_of_hold})
        return {
            'type': 'ir.actions.client',
            'tag': 'reload', }


class SalesChannelPrioritization(models.Model):
    _inherit = "crm.team"
    team_type = fields.Selection([('engine', 'Prioritization'), ('sales', 'Sales'), ('website', 'Website')],
                                 string='Channel Type', default='sales',
                                 required=True,
                                 help="The type of this channel, it will define the resources this channel uses.")


class StockMove(models.Model):
    _inherit = "stock.move"
    partial_UOM = fields.Boolean("Allow Partial UOM?", compute="_get_partial_UOM", readonly=True)
    default_code = fields.Char("SKU", store=False, readonly=True, related='product_id.product_tmpl_id.default_code')

    @api.multi
    def _get_partial_UOM(self):
        for stock_move in self:
            _logger.info('partner id : %r, product id : %r', stock_move.partner_id.id, stock_move.product_id.id)
            if stock_move.partner_id and stock_move.product_id:
                setting = self.env['sps.customer.requests'].get_settings_object(stock_move.partner_id.id,
                                                                                stock_move.product_id.id,
                                                                                None, None)
                if setting:
                    if setting.partial_UOM and not setting.partial_UOM is None:
                        _logger.info('partial UOM** : %r', setting.partial_UOM)
                        stock_move.partial_UOM = setting.partial_UOM

    def _action_assign(self):
        _logger.info('*****prioritization -> _action_assign()*********')
        """ Reserve stock moves by creating their stock move lines. A stock move is
        considered reserved once the sum of `product_qty` for all its move lines is
        equal to its `product_qty`. If it is less, the stock move is considered
        partially available.
        """
        assigned_moves = self.env['stock.move']
        partially_available_moves = self.env['stock.move']

        product_lot_qty_dict = {}
        # product_lot_qty_dict.clear()
        for move in self.filtered(lambda m: m.state in ['confirmed', 'waiting', 'partially_available']):
            product_lot_qty_dict.clear()

            if (move.picking_id and move.picking_id.sale_id) and (
                    move.picking_id.sale_id.team_id.team_type.lower().strip() == 'engine' and move.picking_id.sale_id.state.lower().strip() in (
                    'sale')):
                _logger.info('sales channel is engine')
                available_production_lot_dict = self.env['available.product.dict'].get_available_production_lot_dict()

                # get expiration tolerance
                _setting_object = self.env['sps.customer.requests'].get_settings_object(move.partner_id.id, move.product_id.id, None, None)

                # Search lot Id as per partner product expiration tolerance
                filter_available_product_lot_dict = self.env[
                    'prioritization.engine.model'].filter_available_product_lot_dict(available_production_lot_dict, move.product_id.id, _setting_object.expiration_tolerance)

                for product_lot in filter_available_product_lot_dict.get(move.product_id.id, {}):
                    lot_id = product_lot.get(list(product_lot.keys()).pop(0), {}).get('lot_id')
                    avi_qty = product_lot.get(list(product_lot.keys()).pop(0), {}).get('available_quantity')
                    use_date = product_lot.get(list(product_lot.keys()).pop(0), {}).get('use_date')
                    dict1 = {'lot_id': lot_id, 'available_qty': avi_qty, 'use_date': use_date}

                    if move.product_id.id in product_lot_qty_dict.keys():
                        product_lot_qty_dict.get(move.product_id.id, {}).append(dict1)
                    else:
                        new_dict = {move.product_id.id: [dict1]}
                        product_lot_qty_dict.update(new_dict)

                dict_by_product = product_lot_qty_dict.get(move.product_id.id, {})
                dict_asc_by_use_date = sorted(dict_by_product, key=lambda i: i['use_date'])

                need = move.product_qty - move.reserved_availability
                for prdt_lot_qty in dict_asc_by_use_date:
                    if need > 0:
                        taken_quantity = move._update_reserved_quantity(need, prdt_lot_qty['available_qty'], move.location_id, prdt_lot_qty['lot_id'], strict=False)
                        _logger.info('taken_quantity : %r', taken_quantity)
                        need = need - taken_quantity
            else:
                if move.location_id.should_bypass_reservation() \
                        or move.product_id.type == 'consu':
                    # create the move line(s) but do not impact quants
                    if move.product_id.tracking == 'serial' and (
                            move.picking_type_id.use_create_lots or move.picking_type_id.use_existing_lots):
                        for i in range(0, int(move.product_qty - move.reserved_availability)):
                            self.env['stock.move.line'].create(move._prepare_move_line_vals(quantity=1))
                    else:
                        to_update = move.move_line_ids.filtered(lambda ml: ml.product_uom_id == move.product_uom and
                                                                           ml.location_id == move.location_id and
                                                                           ml.location_dest_id == move.location_dest_id and
                                                                           ml.picking_id == move.picking_id and
                                                                           not ml.lot_id and
                                                                           not ml.package_id and
                                                                           not ml.owner_id)
                        if to_update:
                            to_update[0].product_uom_qty += move.product_qty - move.reserved_availability
                        else:
                            self.env['stock.move.line'].create(
                                move._prepare_move_line_vals(quantity=move.product_qty - move.reserved_availability))
                    assigned_moves |= move
                else:
                    if not move.move_orig_ids:
                        if move.procure_method == 'make_to_order':
                            continue
                        # If we don't need any quantity, consider the move assigned.
                        need = move.product_qty - move.reserved_availability
                        if float_is_zero(need, precision_rounding=move.product_id.uom_id.rounding):
                            assigned_moves |= move
                            continue
                        # Reserve new quants and create move lines accordingly.
                        available_quantity = self.env['stock.quant']._get_available_quantity(move.product_id,
                                                                                             move.location_id)
                        if available_quantity <= 0:
                            continue
                        taken_quantity = move._update_reserved_quantity(need, available_quantity, move.location_id,
                                                                        strict=False)
                        if float_is_zero(taken_quantity, precision_rounding=move.product_id.uom_id.rounding):
                            continue
                        if need == taken_quantity:
                            assigned_moves |= move
                        else:
                            partially_available_moves |= move
                    else:
                        # Check what our parents brought and what our siblings took in order to
                        # determine what we can distribute.
                        # `qty_done` is in `ml.product_uom_id` and, as we will later increase
                        # the reserved quantity on the quants, convert it here in
                        # `product_id.uom_id` (the UOM of the quants is the UOM of the product).
                        move_lines_in = move.move_orig_ids.filtered(lambda m: m.state == 'done').mapped('move_line_ids')
                        keys_in_groupby = ['location_dest_id', 'lot_id', 'result_package_id', 'owner_id']

                        def _keys_in_sorted(ml):
                            return (ml.location_dest_id.id, ml.lot_id.id, ml.result_package_id.id, ml.owner_id.id)

                        grouped_move_lines_in = {}
                        for k, g in groupby(sorted(move_lines_in, key=_keys_in_sorted),
                                            key=itemgetter(*keys_in_groupby)):
                            qty_done = 0
                            for ml in g:
                                qty_done += ml.product_uom_id._compute_quantity(ml.qty_done, ml.product_id.uom_id)
                            grouped_move_lines_in[k] = qty_done
                        move_lines_out_done = (move.move_orig_ids.mapped('move_dest_ids') - move) \
                            .filtered(lambda m: m.state in ['done']) \
                            .mapped('move_line_ids')
                        # As we defer the write on the stock.move's state at the end of the loop, there
                        # could be moves to consider in what our siblings already took.
                        moves_out_siblings = move.move_orig_ids.mapped('move_dest_ids') - move
                        moves_out_siblings_to_consider = moves_out_siblings & (
                                assigned_moves + partially_available_moves)
                        reserved_moves_out_siblings = moves_out_siblings.filtered(
                            lambda m: m.state in ['partially_available', 'assigned'])
                        move_lines_out_reserved = (reserved_moves_out_siblings | moves_out_siblings_to_consider).mapped(
                            'move_line_ids')
                        keys_out_groupby = ['location_id', 'lot_id', 'package_id', 'owner_id']

                        def _keys_out_sorted(ml):
                            return (ml.location_id.id, ml.lot_id.id, ml.package_id.id, ml.owner_id.id)

                        grouped_move_lines_out = {}
                        for k, g in groupby(sorted(move_lines_out_done, key=_keys_out_sorted),
                                            key=itemgetter(*keys_out_groupby)):
                            qty_done = 0
                            for ml in g:
                                qty_done += ml.product_uom_id._compute_quantity(ml.qty_done, ml.product_id.uom_id)
                            grouped_move_lines_out[k] = qty_done
                        for k, g in groupby(sorted(move_lines_out_reserved, key=_keys_out_sorted),
                                            key=itemgetter(*keys_out_groupby)):
                            grouped_move_lines_out[k] = sum(
                                self.env['stock.move.line'].concat(*list(g)).mapped('product_qty'))
                        available_move_lines = {key: grouped_move_lines_in[key] - grouped_move_lines_out.get(key, 0) for
                                                key
                                                in grouped_move_lines_in.keys()}
                        # pop key if the quantity available amount to 0
                        available_move_lines = dict((k, v) for k, v in available_move_lines.items() if v)

                        if not available_move_lines:
                            continue
                        for move_line in move.move_line_ids.filtered(lambda m: m.product_qty):
                            if available_move_lines.get((move_line.location_id, move_line.lot_id,
                                                         move_line.result_package_id, move_line.owner_id)):
                                available_move_lines[
                                    (move_line.location_id, move_line.lot_id, move_line.result_package_id,
                                     move_line.owner_id)] -= move_line.product_qty
                        for (location_id, lot_id, package_id, owner_id), quantity in available_move_lines.items():
                            need = move.product_qty - sum(move.move_line_ids.mapped('product_qty'))
                            # `quantity` is what is brought by chained done move lines. We double check
                            # here this quantity is available on the quants themselves. If not, this
                            # could be the result of an inventory adjustment that removed totally of
                            # partially `quantity`. When this happens, we chose to reserve the maximum
                            # still available. This situation could not happen on MTS move, because in
                            # this case `quantity` is directly the quantity on the quants themselves.
                            available_quantity = self.env['stock.quant']._get_available_quantity(
                                move.product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id,
                                strict=True)
                            if float_is_zero(available_quantity, precision_rounding=move.product_id.uom_id.rounding):
                                continue
                            taken_quantity = move._update_reserved_quantity(need, min(quantity, available_quantity),
                                                                            location_id, lot_id, package_id, owner_id)
                            if float_is_zero(taken_quantity, precision_rounding=move.product_id.uom_id.rounding):
                                continue
                            if need - taken_quantity == 0.0:
                                assigned_moves |= move
                                break
                            partially_available_moves |= move
        partially_available_moves.write({'state': 'partially_available'})
        assigned_moves.write({'state': 'assigned'})
        self.mapped('picking_id')._check_entire_pack()


class GLAccount(models.Model):
    _name = "gl.account"

    _sql_constraints = [
        ('name', 'unique(name)', 'GL Account already exists'),
    ]
    name = fields.Char(string='GL Account', required=True, translate=True)
    partner_id = fields.Many2one('res.partner', string='Partner')

