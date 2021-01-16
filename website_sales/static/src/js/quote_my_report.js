odoo.define('website_sales.quote_my_report_cart', function (require) {
'use strict';

    require('web.dom_ready');
    var base = require("web_editor.base");
    var ajax = require('web.ajax');
    var utils = require('web.utils');
    var core = require('web.core');
    var config = require('web.config');
    require("website.content.zoomodoo");
    var _t = core._t;

    $('#selectAll').click(function (ev) {
        console.log('checked all');
        $(this).closest('table').find('td input:checkbox').prop('checked', this.checked);
        var $link = $(ev.currentTarget);
        var $input = $link.parent().find("input");
        var val = $input.prop('checked')
        ajax.jsonRpc("/shop/quote_my_report/update_json", 'call', {
                        'select': val
                    }).then(function (data) {
                        console.log('return');
                        console.log(data);
            });
    });

	$('.report').each(function () {
	    var engine = this;

        $(engine).on('click', 'a.js_add_cart_json', function (ev) {
            console.log('In add quantity');
            ev.preventDefault();
            var $link = $(ev.currentTarget);
            var $input = $link.parent().find("input");
            var product_id = parseInt($input[0]['attributes']['data-product-id']['value']);
            var new_qty = parseInt($input.val());
            ajax.jsonRpc("/shop/quote_my_report/update_json", 'call', {
                        'product_id': product_id,
                        'new_qty': new_qty,
                    }).then(function (data) {
                        console.log('return');
                        console.log(data);
            });
        });

        $(engine).on('click', 'input:checkbox', function (ev) {
            console.log('checked one');
            var $link = $(ev.currentTarget);
            var $input = $link.parent().find("input");
            if ('data-product-id' in $input[0]['attributes']){
                var product_id = parseInt($input[0]['attributes']['data-product-id']['value']);
                var val = $input.prop('checked')
                ajax.jsonRpc("/shop/quote_my_report/update_json", 'call', {
                            'product_id': product_id,
                            'select': val
                        }).then(function (data) {
                            console.log('return');
                            console.log(data);
                });
            }
        });

   });
});
