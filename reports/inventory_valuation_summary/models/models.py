from odoo import api, fields, models, tools
import logging
import odoo.addons.decimal_precision as dp

_logger = logging.getLogger(__name__)


class InventoryValuationPopUp(models.TransientModel):
    _name = 'popup.inventory.valuation.summary'
    _description = 'Inventory Valuation PopUp'

    property_cost_method = fields.Selection([
        ('standard', 'Standard Price'),
        ('fifo', 'First In First Out (FIFO)'),
        ('average', 'Average Cost (AVCO)')], string="Costing Method")

    warehouse = fields.Many2one('stock.warehouse', string='Warehouse')
    location = fields.Many2one('stock.location', string='Location')
    sku_code = fields.Char('Product SKU')
    asset_value = fields.Char(string="Asset Value")

    def open_table(self):

        tree_view_id = self.env.ref('inventory_valuation_summary.inventory_valuation_summary_list').id
        form_view_id = self.env.ref('inventory_valuation_summary.inventory_valuation_summary_form').id

        res_model = 'report.inventory.valuation.summary'

        # self.env[res_model].delete_and_create()
        action = {
            "type": "ir.actions.act_window",
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            "view_mode": "tree,form",
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


class ReportInventoryValuationSummary(models.Model):
    _name = "report.inventory.valuation.summary"
    _description = "report inventory valuation summary"
    _auto = False

    warehouse = fields.Char(string="Warehouse")
    location = fields.Char(string="Location")
    product_id = fields.Many2one('product.product', string='Product', )
    name = fields.Char(string="Name")
    sku_code = fields.Char('Product SKU')
    quantity = fields.Float(string="Quantity", digits='Product Unit of Measure')
    quantity_cal = fields.Float(string="Quantity", compute='_compute_unit_cost',
                                digits='Product Unit of Measure')
    unit_cost = fields.Float(string="Unit Cost", compute='_compute_unit_cost')
    asset_value = fields.Float(string="Asset Value", store=False)
    type = fields.Char(string="Type")
    currency_id = fields.Many2one('res.currency', string='Currency', store=False)
    cost_method = fields.Char(string="Cost Method", store=False)

    #  @api.model_cr
    def init(self):
        self.init_table()
        # pass

    def init_table(self):
        tools.drop_view_if_exists(self._cr, self._name.replace(".", "_"))

        select_query = """  SELECT  ROW_NUMBER () OVER (ORDER BY warehouse) as id, * From ( """
        # -------------------- purchase ------------------------
        select_query = select_query + """     
            SELECT
                public.stock_warehouse.name                 AS warehouse,
                public.stock_location.name                  AS location,
                public.product_product.id                   AS product_id,
                public.product_template.name                AS name,
                COALESCE(product_template.sku_code, '')     AS sku_code,
                SUM(public.purchase_order_line.product_qty) AS quantity,
                'Purchases'                                 AS type
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
                public.stock_picking.state NOT IN ('done',
                                                   'cancel')
            GROUP BY
                public.stock_warehouse.name,
                public.stock_location.name,
                public.product_product.id,
                public.product_template.name,
                public.product_template.sku_code
                """

        select_query = select_query + """ UNION
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
            INNER JOIN
                public.stock_picking_type
            ON
                (
                    public.stock_picking.picking_type_id = public.stock_picking_type.id)
            WHERE
                stock_picking.state NOT IN ('done',
                                                   'cancel')  AND public.stock_picking_type.code = 'outgoing' 
            GROUP BY
                product_product.id,
                stock_warehouse.name,
                stock_location.name,
                product_template.name,
                product_template.sku_code
                """

        select_query = select_query + """ UNION
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

           Group By 
                product_product.id,
                product_template.name,
                product_template.sku_code,
                stock_location.name,
                stock_warehouse.name
                ) as tbl
               """

        sql_query = "CREATE VIEW " + self._name.replace(".", "_") + " AS ( " + select_query + " )"
        self._cr.execute(sql_query)

    def delete_and_create(self):
        self.init_table()

    def action_valuation_at_date_details(self):
        action = self.product_id.action_valuation_at_date_details()
        action.pop('context')
        return action

    def _compute_unit_cost(self):
        for record in self:
            record.currency_id = record.product_id.currency_id.id

            product_tmpl_id = record.product_id.product_tmpl_id
            record.cost_method = product_tmpl_id.cost_method
            record.unit_cost = product_tmpl_id.standard_price

            if record.type == 'Stock':
                record.quantity_cal = record.quantity - product_tmpl_id.outgoing_qty
            else:
                record.quantity_cal = record.quantity

            record.asset_value = record.unit_cost * record.quantity_cal

