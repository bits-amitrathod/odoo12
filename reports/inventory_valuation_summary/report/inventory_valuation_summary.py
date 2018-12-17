from odoo import api, models


class ReportInventoryProductValuationSummary(models.AbstractModel):
    _name = 'report.inventory_valuation_summary.inventory_valuation_template'

    @api.model
    def get_report_values(self, docids, data=None):
        self.env.cr.execute("""
            SELECT warehouse|| '/'|| location as warehouse, array_agg(ARRAY[ type, products]) as type
            from(SELECT  warehouse, type,location, string_agg(concat_ws('**|**',sku_code, name, quantity,unit_cost,asset_value,currency_id),'||**||') as products
                FROM public.report_inventory_valuation_summary where id in ("""+",".join(map(str, docids))+""") Group by warehouse,type,location) as tbl Group by warehouse,location
                          """)

        warehouses = self.env.cr.dictfetchall()
        return {
            'warehouses': warehouses
        }
