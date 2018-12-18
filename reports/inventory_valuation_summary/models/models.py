from odoo import models, fields
import logging

_logger = logging.getLogger(__name__)


class InventoryValuationPopUp(models.TransientModel):
    _name = 'popup.inventory.valuation.summary'

    property_cost_method = fields.Selection([
        ('standard', 'Standard Price'),
        ('fifo', 'First In First Out (FIFO)'),
        ('average', 'Average Cost (AVCO)')], string="Costing Method")

    warehouse = fields.Many2one('stock.warehouse', string='Warehouse')
    location = fields.Many2one('stock.location', string='Location')
    sku_code = fields.Char('SKU / Catalog No')
    asset_value = fields.Char(string="Asset Value")

    def open_table(self):

        res_model = 'report.inventory.valuation.summary'

        self.env[res_model].delete_and_create()
        action = {
            "type": "ir.actions.act_window",
            "view_mode": "tree",
            "res_model": res_model,
            "name": "Inventory Valuation Summary",
            "context": {"search_default_valuation_summary": 1},
            "domain": []
        }

        if self.property_cost_method:
            action["domain"].append(('cost_method', '=', self.property_cost_method))

        if self.warehouse.id:
            action["domain"].append(('warehouse', '=', self.warehouse.name))

        if self.location.id:
            action["domain"].append(('location', '=', self.location.name))

        if self.sku_code:
            action["domain"].append(('sku_code', 'ilike', self.sku_code))

        if self.asset_value:
            action["domain"].append(('asset_value', '=', float(self.asset_value)))

        return action


class ReportInventoryValuationSummary(models.TransientModel):
    _name = "report.inventory.valuation.summary"
    _description = "report inventory valuation summary"

    warehouse = fields.Char(string="Warehouse")
    location = fields.Char(string="Location")
    product_id = fields.Many2one('product.product', string='Product', )
    name = fields.Char(string="Name")
    sku_code = fields.Char('SKU / Catalog No')
    quantity = fields.Float(string="Quantity")
    unit_cost = fields.Float(string="Unit Cost")
    asset_value = fields.Float(string="Asset Value")
    type = fields.Char(string="Type")
    currency_id = fields.Many2one('res.currency', string='Currency')
    cost_method = fields.Char(string="Cost Method")

    def init(self):
        self.init_table()

    def init_table(self):
        sql_query = """ 
            TRUNCATE TABLE "report_inventory_valuation_summary"
            RESTART IDENTITY;
        """
        self._cr.execute(sql_query)

        # -------------------- purchase ------------------------
        select_query = """
                INSERT INTO report_inventory_valuation_summary  (warehouse, location, product_id,name,sku_code,quantity,unit_cost,asset_value,type)
                    SELECT
                        stock_warehouse.name  AS warehouse,
                        stock_location.name   AS location,
                        product_product.id    AS product_id,
                        product_template.name AS name,
                        COALESCE(product_template.sku_code,'') AS sku_code,
                        purchase_order_line.product_qty as quantity,
                        purchase_order_line.price_unit as unit_cost,
                        purchase_order_line.price_unit * purchase_order_line.product_qty as asset_value,
                        'Purchases' as type
                    FROM
                        purchase_order_line
                    INNER JOIN
                        purchase_order
                    ON
                        (
                            purchase_order_line.order_id = purchase_order.id)
                    INNER JOIN
                        product_product
                    ON
                        (
                            purchase_order_line.product_id = product_product.id)
                    INNER JOIN
                        purchase_order_stock_picking_rel
                    ON
                        (
                            purchase_order.id = purchase_order_stock_picking_rel.purchase_order_id)
                    INNER JOIN
                        stock_picking
                    ON
                        (
                            purchase_order_stock_picking_rel.stock_picking_id = stock_picking.id)
                    INNER JOIN
                        stock_location
                    ON
                        (
                            stock_picking.location_dest_id = stock_location.id)
                    INNER JOIN
                        stock_warehouse
                    ON
                        (
                            stock_location.id = stock_warehouse.lot_stock_id)
                    INNER JOIN
                        product_template
                    ON
                        (
                            product_product.product_tmpl_id = product_template.id)
                    WHERE
                        stock_picking.state  NOT IN ('done', 'cancel')
                """

        self._cr.execute(select_query)

        # -------------------- Sales ------------------------
        select_query = """
                        INSERT INTO report_inventory_valuation_summary  (warehouse, location, product_id,name,sku_code,quantity,type)
                            SELECT DISTINCT
                                stock_warehouse.name as warehouse,
                                stock_location.name as location,
                                product_product.id as product_id,
                                product_template.name as name,
                                COALESCE(product_template.sku_code,'') AS sku_code,
                                SUM(sale_order_line.product_uom_qty) as quantity,
                                'Sales' as type
                               
                            FROM
                                sale_order
                            INNER JOIN
                                stock_warehouse
                            ON
                                (
                                    sale_order.warehouse_id = stock_warehouse.id)
                            INNER JOIN
                                sale_order_line
                            ON
                                (
                                    sale_order.id = sale_order_line.order_id)
                            INNER JOIN
                                stock_picking
                            ON
                                (
                                    sale_order.id = stock_picking.sale_id)
                            INNER JOIN
                                stock_location
                            ON
                                (
                                    stock_picking.location_id = stock_location.id)
                            INNER JOIN
                                product_product
                            ON
                                (
                                    sale_order_line.product_id = product_product.id)
                            INNER JOIN
                                product_template
                            ON
                                (
                                    product_product.product_tmpl_id = product_template.id)
                            WHERE
                                stock_picking.state NOT IN ('done',
                                                                   'cancel')
                            GROUP BY
                                product_product.id,
                                stock_warehouse.name,
                                stock_location.name,
                                product_template.name,
                                product_template.sku_code
                        """

        self._cr.execute(select_query)

        # -------------------- Stock ------------------------
        select_query = """
               INSERT INTO report_inventory_valuation_summary  (warehouse, location, product_id,name,sku_code,quantity,type)
                   SELECT DISTINCT
                       stock_warehouse.name  AS warehouse,
                       stock_location.name   AS location,
                       product_product.id    AS product_id,
                       product_template.name AS name,
                       COALESCE(product_template.sku_code,'') AS sku_code,  
                       SUM(stock_quant_alias1.quantity) as quantity,
                       'Stock' as type
                   FROM
                       product_product
                   INNER JOIN
                       product_template
                   ON
                       (
                           product_product.product_tmpl_id = product_template.id)
                   INNER JOIN
                       stock_quant stock_quant_alias1
                   ON
                       (
                           product_product.id = stock_quant_alias1.product_id)
                   INNER JOIN
                       stock_location
                   ON
                       (
                           stock_quant_alias1.location_id = stock_location.id)
                   INNER JOIN
                       stock_warehouse
                   ON
                       (
                           stock_location.id = stock_warehouse.lot_stock_id)
                   INNER JOIN
                       stock_production_lot
                   ON
                       (stock_quant_alias1.lot_id = stock_production_lot.id) 

                   Group By 
                        product_product.id,
                        product_template.name,
                        product_template.sku_code,
                        stock_location.name,
                        stock_warehouse.name;
               """

        self._cr.execute(select_query)

        invModel = self.env[self._name].search([])
        productCount = {}
        productAmount = {}

        for record in invModel:
            data = {'currency_id': record.product_id.currency_id.id,
                    'cost_method': record.product_id.product_tmpl_id.cost_method}

            if record.type == 'Purchases':
                if record.product_id.id in productCount:
                    productCount[record.product_id.id] = productCount[record.product_id.id] + record.quantity
                else:
                    productCount[record.product_id.id] = record.quantity

                if record.product_id.id in productAmount:
                    productAmount[record.product_id.id] = productAmount[record.product_id.id] + record.unit_cost
                else:
                    productAmount[record.product_id.id] = record.unit_cost

            if record.type == 'Stock':
                data['unit_cost'] = record.product_id.product_tmpl_id.standard_price
                data['asset_value'] = record.product_id.stock_value
                data['quantity'] = record.quantity

                if record.product_id.id in productCount:
                    data['quantity'] = data['quantity'] - productCount[record.product_id.id]

                if record.product_id.id in productAmount:
                    data['asset_value'] = data['asset_value'] - productAmount[record.product_id.id]

            if record.type == 'Sales':
                data['unit_cost'] = 0
                data['asset_value'] = 0

            record.write(data)

    def delete_and_create(self):
        self.init_table()

    def action_valuation_at_date_details(self):
        action = self.product_id.action_valuation_at_date_details()
        action.pop('context')
        return action
