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
        var val = $input.prop('checked');

        if (val === true){
            $('[id^=allow_qty_plus_]').css({'pointer-events':'', 'color':'#1b1717'});
            $('[id^=allow_qty_minus_]').css({'pointer-events':'', 'color':'#1b1717'});
        } else {
            $('[id^=allow_qty_plus_]').css({'pointer-events':'none', 'color':'#cacaca'});
            $('[id^=allow_qty_minus_]').css({'pointer-events':'none', 'color':'#cacaca'});
        }

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
            var available_qty = parseInt($input[0]['attributes']['data-available-qty']['value']);
            var partn_name_id = $input[0]['attributes']['data-partn-name-id']['value'];
            var new_qty = parseInt($input.val());
            console.log(partn_name_id);
            var ele1 = $link.parent().find("#allow_qty_plus_"+partn_name_id);
            if (available_qty === new_qty) {
                $('#allow_qty_plus_'+partn_name_id).css({'pointer-events':'none'});
            }else{
                $('#allow_qty_plus_'+partn_name_id).css({'pointer-events':''});
            }

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
            if ('data-partn-name-id' in $input[0]['attributes']) {
                var partn_name_id = parseInt($input[0]['attributes']['data-partn-name-id']['value']);
                var available_qty = parseInt($input[0]['attributes']['data-available-qty']['value']);
                var new_qty = parseInt($('#input_qty_'+partn_name_id).val());
                var val = $input.prop('checked');

                if(val === true){
                    if (available_qty != new_qty) {
                        $('#allow_qty_plus_'+partn_name_id).css({'pointer-events':'', 'color':'#1b1717'});
                    }
                    $('#allow_qty_minus_'+partn_name_id).css({'pointer-events':'', 'color':'#1b1717'});

                }else{
                    $('#allow_qty_plus_'+partn_name_id).css({'pointer-events':'none', 'color':'#cacaca'});
                    $('#allow_qty_minus_'+partn_name_id).css({'pointer-events':'none', 'color':'#cacaca'});
                }
            }

            if ($('td input:checked').length > 0) {
                $("#add_product_in_to_cart").attr('disabled', false);
            } else {
                $("#add_product_in_to_cart").attr('disabled', true);
            }

            if ('data-product-id' in $input[0]['attributes']){
                var product_id = parseInt($input[0]['attributes']['data-product-id']['value']);
                var val = $input.prop('checked')

                if(val === false){
                    $('#selectAll').prop('checked', false);
                }

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
