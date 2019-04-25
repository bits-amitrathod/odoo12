odoo.define('vendor_offer.tree_view_button_ven_pri', function (require){
"use strict";


var core = require('web.core');
var ListView = require('web.ListView');
var session = require('web.session');
var time = require('web.time');
var Widget = require('web.Widget');
var ajax = require('web.ajax');
var WebClient = require('web.WebClient');
var ListController = require('web.ListController');
var rpc = require('web.rpc')
var framework = require('web.framework');
var QWeb = core.qweb;


var ImportViewVen = {
    init: function (viewInfo, params) {
        var showPPVendorButton = 'import_enabled' in params ? params.import_enabled : false;
        this.controllerParams.showPPVendorButton = showPPVendorButton;
    },
};

var ImportControllerVen = {
    init: function (parent, model, renderer, params) {
        this.showPPVendorButton = params.showPPVendorButton;
    },
    _bindVendorPri: function () {
     if (!this.$buttons) {
            return;
        }
       var self = this;

        this.$buttons.on('click', '.o_list_ppvendor_button_download', function () {
        framework.blockUI();
        rpc.query({
            model: 'vendor.pricing',
            method: 'download_excel_ven_price',
           args: [{
                'arg1': '',
                'arg2': '',
            }]
        }).then(
                function( returned_value ){
                       self.getSession().get_file({
                        url: '/web/PPVendorPricing/download_document',

                    });
                        framework.unblockUI()
                })
           });
    }
};

ListView.include({
    init: function () {
        this._super.apply(this, arguments);
        ImportViewVen.init.apply(this, arguments);
    },
});

ListController.include({
    init: function () {
        this._super.apply(this, arguments);
        ImportControllerVen.init.apply(this, arguments);
    },
    renderButtons: function () {
        this._super.apply(this, arguments);
        ImportControllerVen._bindVendorPri.call(this);
    }


});

});

