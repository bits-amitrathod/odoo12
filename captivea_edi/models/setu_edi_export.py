from odoo import fields, models, api


class POACKExport(models.Model):
    _name = 'setu.poack.export.log.line'

    accounting_id = fields.Char('Accounting ID')
    vendor_part = fields.Char('Vendor Part')
    po_number = fields.Char('EDI Ref')
    po_date = fields.Char('PO Date')
    company_id = fields.Many2one('res.company', string='Selling Party Name')
    street = fields.Char(related='company_id.street', string='Selling Party Address 1')
    street2 = fields.Char(related='company_id.street2', string='Selling Party Address 2')
    city = fields.Char(related='company_id.city', string='Selling Party City')
    state = fields.Many2one(related='company_id.state_id', string='Selling Party State')
    country = fields.Many2one(related='company_id.country_id', string='Selling Party Country')
    zip = fields.Char(related='company_id.zip', string='Selling Party Zip')
    x_edi_po_line_number = fields.Char('PO Line #')
    product_template_id = fields.Many2one('product.template', 'Vendor Part #')
    qty = fields.Float('Qty')
    uom = fields.Char('UOM')
    price_unit = fields.Float('Price')
    commitment_date = fields.Char(string='Scheduled Delivery Date')
    x_edi_status = fields.Selection([('accept', 'Accept'), ('reject', 'Reject')], string='Status')
    product_uom_qty = fields.Float('Status Qty')
    product_uom = fields.Char('Status UOM')
    edi_log_id = fields.Many2one('setu.edi.log')
    log_type = fields.Selection([('success', 'Success'),
                                 ('fail', 'Failure')])
    upc_num = fields.Char('Barcode')
    transaction_id = fields.Char('Transaction ID', default='855')
    store_number = fields.Char('Store number')
    line_num = fields.Char('PO Line #')
    sale_line_id = fields.Many2one('sale.order.line')
    buyer_part_number = fields.Char()
    x_hdr_ref1 = fields.Char('Order Ref')
    x_hdr_ref2 = fields.Char('GHX Order')


class SHIPACKExport(models.Model):
    _name = 'setu.shipack.export.log.line'

    upc = fields.Char()

    picking_id = fields.Many2one('stock.picking')
    edi_log_id = fields.Many2one('setu.edi.log', 'Log Id')
    accounting_id = fields.Char('Accounting ID')
    shipment_id = fields.Char('Shipment ID')
    x_studio_scac = fields.Char('SCAC')
    carrier_tracking_ref = fields.Char('Carrier Pro #')
    origin_sale_order = fields.Many2one('sale.order', 'Bill of Lading')
    date_done = fields.Char(string='Ship Date')
    store_number = fields.Char('Store number', related='picking_id.partner_id.x_edi_store_number')

    ship_to_name = fields.Char('Ship To Name')
    ship_to_address_1 = fields.Char('Ship To Address – Line One')
    ship_to_address_2 = fields.Char('Ship To Address – Line Two')
    ship_to_city = fields.Char('Ship to city')
    ship_to_state = fields.Char('Ship to state')
    ship_to_zip = fields.Char('Ship to zip')
    ship_to_country = fields.Char('Ship to country')

    carrier_id = fields.Many2one('delivery.carrier', 'Ship via')
    x_studio_edi_packaging_type = fields.Selection([('Pallet', 'Pallet'), ('Carton', 'Carton')],
                                                   string='Packaging Type')
    weight = fields.Float('Gross Weight')
    weight_uom_name = fields.Char('')
    x_studio_edi_carton_count = fields.Integer('# of Cartons Shipped')
    store_name = fields.Char('Store Name')

    ship_from_company_id = fields.Many2one('res.company', 'Ship From Name')
    ship_from_warehouse = fields.Many2one('stock.warehouse')
    ship_from = fields.Many2one(related='ship_from_warehouse.partner_id')
    ship_from_street = fields.Char(related='ship_from.street', string='Ship From Address – Line One')
    ship_from_street2 = fields.Char(related='ship_from.street', string='Ship From Address – Line Two')
    ship_from_city = fields.Char(related='ship_from.city', string='Ship From City')
    ship_from_state = fields.Char(related='ship_from.state_id.name', string='Ship From State')
    ship_from_zip = fields.Char(related='ship_from.zip', string='Ship From Zip')
    ship_from_country = fields.Char(related='ship_from.country_id.name', string='Ship From Country')

    vendor_number = fields.Char('Vendor Number')
    uom = fields.Char('UOM')
    status = fields.Selection([('partial', 'Partial Shipment'),
                               ('complete', 'Shipment Complete')])
    po_number = fields.Char('PO Number')
    po_date = fields.Char('PO Date')
    product_id = fields.Char('Vendor Part Number')
    description_sale = fields.Char('Item Description')
    quantity_done = fields.Float('Quantity Shipped')
    product_uom_quantity = fields.Float('Quantity Ordered')
    ship_via = fields.Char()
    ucc_128 = fields.Char()
    upc_within_pack = fields.Char()
    uom_of_upc = fields.Char()
    buyer_part_number = fields.Char()
    unit_price = fields.Float()

    x_edi_ship_to_type = fields.Selection([('DC', 'Warehouse Number'), ('SN', 'Store Number')], string='Ship To Type')


class INVACKExport(models.Model):
    _name = 'setu.invack.export.log.line'

    x_edi_ship_to_type = fields.Selection([('DC', 'Warehouse Number'), ('SN', 'Store Number')], string='Ship To Type')
    x_edi_transaction_type = fields.Char('Transaction Type')
    invoice_name = fields.Char(related='edi_log_id.invoice_id.name')
    invoice_date = fields.Date(related='edi_log_id.invoice_id.invoice_date')
    bill_of_landing = fields.Char(related='edi_log_id.invoice_id.invoice_origin')

    x_edi_accounting_id = fields.Char(related='edi_log_id.invoice_id.x_edi_accounting_id', string='Accounting ID')
    x_studio_edi_reference = fields.Char(related='edi_log_id.invoice_id.x_studio_edi_reference', string='EDI Reference',
                                         help="po #")
    x_edi_store_number = fields.Char(related='edi_log_id.invoice_id.x_edi_store_number', string='Store Number')
    edi_log_id = fields.Many2one('setu.edi.log')
    ship_via = fields.Char()
    ship_date = fields.Char()
    po_date = fields.Char()
    carrier_tracking_ref = fields.Char()
    scac = fields.Char()
    carrier_id = fields.Many2one('delivery.carrier')
    ship_to_name = fields.Many2one('res.partner')
    ship_to_address_1 = fields.Char(related='ship_to_name.street')
    ship_to_address_2 = fields.Char(related='ship_to_name.street2')
    ship_to_city = fields.Char(related='ship_to_name.city')
    ship_to_state = fields.Char(related='ship_to_name.state_id.name')
    ship_to_country = fields.Char(related='ship_to_name.country_id.name')
    ship_to_zip = fields.Char(related='ship_to_name.zip')

    bill_to_name = fields.Many2one('res.partner')
    bill_to_address_1 = fields.Char(related='bill_to_name.street')
    bill_to_address_2 = fields.Char(related='bill_to_name.street2')
    bill_to_city = fields.Char(related='bill_to_name.city')
    bill_to_state = fields.Char(related='bill_to_name.state_id.name')
    bill_to_country = fields.Char(related='bill_to_name.country_id.name')
    bill_to_zip = fields.Char(related='bill_to_name.zip')

    bill_to_code = fields.Char()

    invoice_payment_term_id = fields.Many2one('account.payment.term')
    amount_by_group = fields.Char(string='Tax Amount')
    vendor_part = fields.Char(string='Vendor Part #')
    buyer_part = fields.Char(string='Buyer Part #')
    upc = fields.Char(string='UPC #')
    description = fields.Char(string='Description')
    qty_shipped = fields.Float(string='QTY Shipped')
    qty_ordered = fields.Float(string='QTY Ordered')
    uom = fields.Char('UOM')
    unit_price = fields.Float('Unit Price')

    net_days_due = fields.Char()
    discount_days_due = fields.Char()
    discount_percent = fields.Char()

    allowance_percent_1 = fields.Char('Allowance percent 1')
    allowance_amount_1 = fields.Char('Allowance amount 1')
    allowance_percent_2 = fields.Char('Allowance percent 2')
    allowance_amount_2 = fields.Char('Allowance amount 2')
    charge_amount_1 = fields.Char('Charge Amount 1')
    charge_amount_2 = fields.Char('Charge Amount 2')
