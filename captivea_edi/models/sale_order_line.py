from odoo import fields, models, api


class SaleOrderLine(models.Model):
    _inherit = ['sale.order.line']

    edi_id = fields.Many2one('setu.edi.log', string='EDI ID', copy=False)
    price_unit_850 = fields.Float('850 Unit Price')
    x_edi_mismatch = fields.Boolean('EDI Mismatch', compute='_compute_edi_price_mismatch', readonly=True)
    x_edi_po_line_number = fields.Char('PO #', readonly=True)
    x_edi_status = fields.Selection([('accept', 'Accept'), ('reject', 'Reject')], string='Status')
    upc_num = fields.Char('Barcode')
    po_log_line_id = fields.Many2one('captivea.edidocumentlog', copy=False)
    initial_product_uom_qty = fields.Float()
    ack_code = fields.Selection([('IA', 'Acceptance'),
                                 ('IP', 'Accepted with price changes'),
                                 ('IC', 'Substitution'),
                                 ('BP', 'Partial Shipment'),
                                 ('IB', 'Back Order'),
                                 ('IR', 'Rejected')], default="IA", string="Ack Code")

    def set_ack_code_to_edi_sales(self):
        query = """
                update sale_order_line
                set ack_code = 'IP'
                where id in                
                (select sol.id from sale_order_line sol
                inner join sale_order so on so.id = sol.order_id
                where so.state not in ('sale','done','cancel')
                and sol.price_unit_850 != 0
                and sol.price_unit_850 != sol.price_unit
                and so.customer_po_ref is not null
                and sol.ack_code != 'IP');
                """
        self._cr.execute(query)
        self._cr.commit()
        query = """
                update sale_order_line
                set ack_code = 'IR'
                where id in                
                (select sol.id from sale_order_line sol
                inner join sale_order so on so.id = sol.order_id
                where so.state not in ('sale','done','cancel')
                and (sol.product_id is null or sol.display_type = 'line_note')
                and so.customer_po_ref is not null
                and sol.ack_code != 'IR');
                """
        self._cr.execute(query)
        self._cr.commit()


    def set_po_line_number(self):
        for line in self:
            if not line.po_log_line_id or not line.po_log_line_id.line_num:
                count = 1
                for id in self.ids:
                    if id < line.id:
                        count += 1
                if line.order_id.order_of == 'ghx':
                    count = str(count)
                    num_of_zero = '000' if len(count) == 1 else '00' if len(count) == 2 else '0' if len(
                        count) == 3 else ''
                    count = num_of_zero + count
                line.x_edi_po_line_number = count

    @api.onchange('price_unit', 'price_unit_850')
    def _compute_edi_price_mismatch(self):
        for rec in self:
            if rec.price_unit == rec.price_unit_850:
                rec.x_edi_mismatch = False
            else:
                rec.x_edi_mismatch = True
