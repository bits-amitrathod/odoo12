odoo.define('in_stock_report_button', function (require) {
"use strict";

    var core = require('web.core');
    var framework = require('web.framework');
    var ListController = require('web.ListController');

    ListController.include({

//        _getActionMenuItems: function (state) {
//            if (!this.hasActionMenus || !this.selectedRecords.length) {
//                return null;
//            }
//            const props = this._super(...arguments);
//            const otherActionItems = [];
//            if (this.modelName == "report.in.stock.report"){
//                if (this.isExportEnable) {
//                    otherActionItems.push({
//                         description: _t("Export Report"),
//                        callback: this.sps_export_instock_report.bind(this)
//                    });
//                }
//            }
//            return Object.assign(props, {
//                items: Object.assign({}, this.toolbarActions, { other: otherActionItems }),
//                context: state.getContext(),
//                domain: state.getDomain(),
//                isDomainSelected: this.isDomainSelected,
//            });
//        },
//
//        sps_export_instock_report: function() {
//            this.in_stock_report_export(this.getSelectedIds());
//        },

        renderButtons: function($node) {
            this._super.apply(this, arguments);
            if (this.$buttons) {
                let filter_button = this.$buttons.find('.o_list_export_button');
                filter_button && filter_button.click(this.proxy('filter_button'));
            }

        },



        filter_button: function () {
         console.log("------------343aa-----------")
            framework.blockUI();
           this.getSession().get_file({
                url: '/web/export/in_stock_report',
                complete: framework.unblockUI,
                error: (error) => this.call('crash_manager', 'rpc_error', error),
                success: function(){
                    console.log("------------aa-----------")
                    framework.unblockUI()
                }
            })

        }

    });

})

