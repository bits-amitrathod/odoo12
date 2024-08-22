/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import {KsGraphPreview} from '@ks_dashboard_ninja/js/ks_dashboard_ninja_graph_preview';


//    var KsGraphPreview = require('ks_dashboard_ninja_list.ks_dashboard_graph_preview');
patch(KsGraphPreview.prototype,"ks_dn_advance", {

        _Ks_render(){
        $(this.input.el.parentElement).find('div').remove()
        $(this.input.el.parentElement).find('input').addClass('d-none')
        var rec = this.props.record.data;
            if (rec.ks_dashboard_item_type !== 'ks_tile' && rec.ks_dashboard_item_type !== 'ks_kpi' && rec.ks_dashboard_item_type !== 'ks_list_view') {
                if(rec.ks_data_calculation_type !== "query"){
                    this._super(...arguments);
                }
                else if(rec.ks_data_calculation_type === "query" && rec.ks_query_result) {
                    if(rec.ks_xlabels && rec.ks_ylabels){
                            this._getChartData();
                    } else {
                        $(this.input.el.parentElement).append($('<div>').text("Please choose the X-labels and Y-labels"));
                    }
                } else {
                    $(this.input.el.parentElement).append($('<div>').text("Please run the appropriate Query"));
                }
            }
        },
    });
