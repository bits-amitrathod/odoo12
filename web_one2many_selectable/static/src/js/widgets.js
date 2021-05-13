odoo.define('web_one2many_selectable.form_widgets', function (require) {
"use strict";

/**
 * This file defines a client action that opens in a dialog (target='new') and
 * allows the user to change his password.
 */
var core = require('web.core');
var ActionManager = require('web.ActionManager');
var Widget = require('web.Widget');
var AbstractField = require('web.AbstractField');
var web_client = require('web.web_client');
var fieldRegistry = require('web.field_registry');
var FieldOne2Many = require('web.relational_fields').FieldOne2Many;
//var FieldOne2Many=fieldRegistry.get("one2many");
var dialogs = require('web.view_dialogs');
var rpc = require('web.rpc')
var _t = core._t;
var One2ManySelectable = FieldOne2Many.extend({
    template: "One2ManySelectable",

    events: {
        "click .cf_button_confirm": "action_selected_lines",
        "click .cf_button_import": "searchCreatePopup",
    },

    start: function () {
        console.log("inside start");
        //this._super.apply(this, arguments);
//        var result = this._super.apply(this, arguments);
//        console.log(result);
//    	return result;
    	return this._super.apply(this, arguments);
    },

   _render: function () {
          this._super.apply(this, arguments);
          if(!this.renderer.hasSelectors){
            this.renderer.hasSelectors=true;
          }
   },
    action_selected_lines: function(e)
	{
			var self=this;
			var ids=[];
			var flag=false
			var records=this.recordData.prioritization_ids.data

			var selected_ids = this.renderer.selection;
			if (selected_ids.length === 0)
			{
				this.do_warn(_t("You must choose at least one record."));
				return false;
			}

            selected_ids.forEach(function(seletedId) {
              records.forEach(function(record) {

                    if(record.id==seletedId){
                        //console.log("Inside If");
                        //console.log(record.res_id);
                        if(record.res_id===undefined){
                                //console.log("Inside If1");
                                flag=true
                                //this.do_warn(_t("You must save the record before Copy Down."));
				            //return false;
                        }else{
                             //console.log("Inside else");
                             ids.push(record.res_id);
                        }

			        }
              });
            });
            if (flag)
			{
				this.do_warn(_t("You must save the record before Multiple Update."));
				return false;
			}
            e.preventDefault();
            var returnVal=this.do_action({
                name: _t("Multiple Update"),
                type: "ir.actions.act_window",
                res_model: "prioritization.transient",
                domain : [],
                views: [[false, "form"]],
                target: 'new',
                context: {'selected_ids':ids},
                view_mode : 'form',
                view_type: "form",
            });
		},


	reinitialize: function (value) {
        this.isDirty = false;
        this.floating = false;
        this._setValue(value);
    },
     searchCreatePopup: function (view, ids, context) {
        var self = this;
        var cust_id=this.res_id;
        var action_manager = new ActionManager(this);
        return new dialogs.SelectCreateDialog(this, _.extend({}, this.nodeOptions, {
            res_model: 'product.product',
            context: _.extend({}, this.record.getContext(this.recordParams), context || {}),
            title: "Multiple Selection",
            initial_ids: ids ? _.map(ids, function (x) { return x[0]; }) : undefined,
            initial_view: 'search',
            //disable_multiple_selection: true,
            on_selected: function (records) {
            rpc.query({
            model: 'prioritization_engine.prioritization',
            method: 'import_product',
            args: [this.res_id, records,cust_id]
        }).then(function (returned_value) {
              action_manager.do_action({type: 'ir.actions.client',tag: 'reload'});
             //,{type: 'ir.actions.client',tag: 'reload'}{'type': 'ir.actions.act_close_wizard_and_reload_view'}
        })
            }
        })).open();
    },

});
fieldRegistry.add("one2many_selectable", One2ManySelectable);
return {
    One2ManySelectable: One2ManySelectable,
};

});