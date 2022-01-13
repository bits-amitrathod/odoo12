import pysftp
from odoo import fields, models, api


class EDILog(models.Model):
    _name = 'setu.edi.log'
    _description = '855 Import Log Lines'
    _rec_name = 'seq'
    _order = 'id desc'

    company_id = fields.Many2one('res.company')
    exception = fields.Text()
    seq = fields.Char(readonly=True, string='Log')
    log_created_from = fields.Selection([('running', 'Running Process'),
                                         ('scheduler', 'Scheduler Process'),
                                         ('manual', 'Manual Process')], default='running')
    edi_log_line_ids = fields.One2many('captivea.edidocumentlog', 'edi_log_id')
    edi_855_log_lines = fields.One2many('setu.poack.export.log.line', 'edi_log_id')
    edi_856_log_lines = fields.One2many('setu.shipack.export.log.line', 'edi_log_id')
    edi_810_log_lines = fields.One2many('setu.invack.export.log.line', 'edi_log_id')
    type = fields.Selection([('import', 'Import'), ('export', 'Export')])
    po_number = fields.Char()
    po_date = fields.Char()
    document_type = fields.Selection([('850', '850 Customer PO'),
                                      ('855', '855 POACK'),
                                      ('810', '810 INVACK'),
                                      ('856', '856 SHIPACK')])
    status = fields.Selection([('fail', 'Fail'), ('success', 'Success')],
                              compute='_compute_log_status', store=True)
    sale_id = fields.Many2one('sale.order', string='Sale Order')
    picking_ids = fields.Many2many('stock.picking', string='Delivery Order')
    invoice_id = fields.Many2one('account.move', string='Invoice')
    file_ref = fields.Char('File Name')
    x_hdr_ref1 = fields.Char('Order Ref')
    x_hdr_ref2 = fields.Char('Total Amount')
    x_hdr_ref3 = fields.Char('Ref 3')
    x_hdr_ref4 = fields.Char('Ref 4')
    x_hdr_ref5 = fields.Char('Ref 5')
    x_lin_ref1 = fields.Char('Line Ref 1')
    x_lin_ref2 = fields.Char('Line Ref 2')
    x_lin_ref3 = fields.Char('Line Ref 3')
    x_lin_ref4 = fields.Char('Line Ref 4')
    x_lin_ref5 = fields.Char('Line Ref 5')
    x_hdr_ref3 = fields.Char('Ref 3')
    x_hdr_ref4 = fields.Char('Ref 4')
    x_hdr_ref5 = fields.Char('Ref 5')

    @api.model_create_multi
    def create(self, vals_list):
        vals_list[0].update({
            'seq': self.env['ir.sequence'].next_by_code('edi.log.seq') or 'LOG/UNKNOWN'
        })
        return super(EDILog, self).create(vals_list)

    @api.depends('edi_log_line_ids.log_type')
    def _compute_log_status(self):
        for log in self:
            if log.document_type == '850':
                states = log.edi_log_line_ids.mapped('log_type')
                if 'fail' not in states and 'success' in states:
                    log.status = 'success'
                if 'fail' in states:
                    log.status = 'fail'

    def get_edi_status(self, lines):
        """
        Will get status of line. 'accept' or 'reject'.

        @param lines: order_lines from sale order.
        @return:
        """
        prod_qty_available_dict = {}
        for line in lines:
            if line.product_id not in prod_qty_available_dict:
                prod_qty_available_dict.update({
                    line.product_id: line.product_id.qty_available
                })
            if line.product_uom_qty <= prod_qty_available_dict[line.product_id]:
                line.x_edi_status = 'accept'
                prod_qty_available_dict[line.product_id] -= line.product_uom_qty
            else:
                line.x_edi_status = 'reject'
                line.product_uom_qty = 0

    # def create_poack_export_log(self, sale_id):
    #     """
    #     Will create 855 type of log.
    #
    #     @param sale_id: sale_id whose log is to be created.
    #     @return: log_id: log_id of sale_id.
    #     """
    #     sale_order = self.env['sale.order'].browse(sale_id)
    #     log_id = self.create({
    #         'po_number': sale_order.x_edi_reference,
    #         'type': 'export',
    #         'document_type': '855',
    #         'sale_id': sale_id
    #     })
    #     export_log = self.env['setu.poack.export.log.line']
    #     for line in sale_order.order_line:
    #         export_log.create({
    #             'accounting_id': sale_order.x_edi_accounting_id,
    #             'po_number': sale_order.x_edi_reference,
    #             'po_date': str(sale_order.date_order.date()) or str(
    #                 sale_order.customer_po_ref.po_date),
    #             'company_id': sale_order.company_id.id,
    #             'x_edi_po_line_number': line.x_edi_po_line_number,
    #             'product_template_id': line.product_template_id.id,
    #             'qty': line.po_log_line_id.quantity,
    #             'uom': line.po_log_line_id.uom,
    #             'price_unit': line.price_unit,
    #             'commitment_date': str(sale_order.order_line[0].po_log_line_id.ship_date) if sale_order.order_line and
    #                                                                                          sale_order.order_line[
    #                                                                                              0] and
    #                                                                                          sale_order.order_line[
    #                                                                                              0].po_log_line_id and
    #                                                                                          sale_order.order_line[
    #                                                                                              0].po_log_line_id.ship_date
    #             else sale_order.commitment_date.date() if sale_order.commitment_date else False,
    #             'x_edi_status': line.x_edi_status,
    #             'product_uom_qty': line.product_uom_qty,
    #             'product_uom': line.product_uom.name,
    #             'edi_log_id': log_id.id,
    #             'line_num': line.x_edi_po_line_number,
    #             'upc_num': line.product_id.barcode or line.upc_num
    #         })
    #     return log_id
