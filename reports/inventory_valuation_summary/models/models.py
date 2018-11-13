from odoo import models, fields
import logging

_logger = logging.getLogger(__name__)


class ReportInventoryValuationSummary(models.TransientModel):
    _name = "inventory.valuation.summary"
    _description = "report inventory valuation summary"

    warehouse = fields.Char(string="Warehouse")
    location = fields.Char(string="Location")
    product_id = fields.Many2one('product.product', string='Product', )
    name = fields.Char(string="Name")
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
            TRUNCATE TABLE "inventory_valuation_summary"
            RESTART IDENTITY;
        """
        self._cr.execute(sql_query)

        # -------------------- purchase ------------------------
        sql_query = """
                INSERT INTO inventory_valuation_summary  (warehouse, location, product_id,name,quantity,unit_cost,asset_value,type)
                    SELECT
                        public.stock_warehouse.name  AS warehouse,
                        public.stock_location.name   AS location,
                        public.product_product.id    AS product_id,
                        public.product_template.name AS name,
                        public.purchase_order_line.product_qty as quantity,
                        public.purchase_order_line.price_unit as unit_cost,
                        purchase_order_line.price_unit * purchase_order_line.product_qty as asset_value,
                        'Purchases' as type
                    FROM
                        public.purchase_order_line
                    INNER JOIN
                        public.purchase_order
                    ON
                        (
                            public.purchase_order_line.order_id = public.purchase_order.id)
                    INNER JOIN
                        public.product_product
                    ON
                        (
                            public.purchase_order_line.product_id = public.product_product.id)
                    INNER JOIN
                        public.purchase_order_stock_picking_rel
                    ON
                        (
                            public.purchase_order.id = public.purchase_order_stock_picking_rel.purchase_order_id)
                    INNER JOIN
                        public.stock_picking
                    ON
                        (
                            public.purchase_order_stock_picking_rel.stock_picking_id = public.stock_picking.id)
                    INNER JOIN
                        public.stock_location
                    ON
                        (
                            public.stock_picking.location_dest_id = public.stock_location.id)
                    INNER JOIN
                        public.stock_warehouse
                    ON
                        (
                            public.stock_location.id = public.stock_warehouse.lot_stock_id)
                    INNER JOIN
                        public.product_template
                    ON
                        (
                            public.product_product.product_tmpl_id = public.product_template.id)
                    WHERE
                        public.stock_picking.state  NOT IN ('done', 'cancel')
                """

        self._cr.execute(sql_query)

        # -------------------- Sales ------------------------
        sql_query = """
                        INSERT INTO inventory_valuation_summary  (warehouse, location, product_id,name,quantity,type)
                            SELECT DISTINCT
                                public.stock_warehouse.name as warehouse,
                                public.stock_location.name as location,
                                public.product_product.id as product_id,
                                public.product_template.name as name,
                                SUM(public.sale_order_line.product_uom_qty) as quantity,
                                'Sales' as type
                               
                            FROM
                                public.sale_order
                            INNER JOIN
                                public.stock_warehouse
                            ON
                                (
                                    public.sale_order.warehouse_id = public.stock_warehouse.id)
                            INNER JOIN
                                public.sale_order_line
                            ON
                                (
                                    public.sale_order.id = public.sale_order_line.order_id)
                            INNER JOIN
                                public.stock_picking
                            ON
                                (
                                    public.sale_order.id = public.stock_picking.sale_id)
                            INNER JOIN
                                public.stock_location
                            ON
                                (
                                    public.stock_picking.location_id = public.stock_location.id)
                            INNER JOIN
                                public.product_product
                            ON
                                (
                                    public.sale_order_line.product_id = public.product_product.id)
                            INNER JOIN
                                public.product_template
                            ON
                                (
                                    public.product_product.product_tmpl_id = public.product_template.id)
                            WHERE
                                public.stock_picking.state NOT IN ('done',
                                                                   'cancel')
                            GROUP BY
                                public.product_product.id,
                                public.stock_warehouse.name,
                                public.stock_location.name,
                                public.product_template.name
                        """

        self._cr.execute(sql_query)

        # -------------------- Stock ------------------------
        sql_query = """
               INSERT INTO inventory_valuation_summary  (warehouse, location, product_id,name,quantity,type)
                   SELECT DISTINCT
                       stock_warehouse.name  AS warehouse,
                       stock_location.name   AS location,
                       product_product.id    AS product_id,
                       product_template.name AS name,  
                       SUM(stock_quant_alias1.quantity) as quantity,
                       'Stock' as type
                   FROM
                       public.product_product
                   INNER JOIN
                       public.product_template
                   ON
                       (
                           public.product_product.product_tmpl_id = public.product_template.id)
                   INNER JOIN
                       public.stock_quant stock_quant_alias1
                   ON
                       (
                           public.product_product.id = stock_quant_alias1.product_id)
                   INNER JOIN
                       public.stock_location
                   ON
                       (
                           stock_quant_alias1.location_id = public.stock_location.id)
                   INNER JOIN
                       public.stock_warehouse
                   ON
                       (
                           public.stock_location.id = public.stock_warehouse.lot_stock_id)
                   INNER JOIN
                       public.stock_production_lot
                   ON
                       (stock_quant_alias1.lot_id = public.stock_production_lot.id) 

                           Group By 
                           public.product_product.id,
                           public.product_template.name,
                           public.stock_location.name,
                           public.stock_warehouse.name;
               """

        self._cr.execute(sql_query)

        invModel = self.env['inventory.valuation.summary'].search([])
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

        return {
            "type": "ir.actions.act_window",
            "view_mode": "tree",
            "res_model": self._name,
            "name": "Inventory Valuation Summary",
            "context": {"search_default_valuation_summary": 1}
        }

    def action_valuation_at_date_details(self):
        action = self.product_id.action_valuation_at_date_details()
        action.pop('context')
        return action
