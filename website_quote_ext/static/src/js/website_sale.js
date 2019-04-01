odoo.define('website_quote_ext._ex', function (require) {
    "use strict";

    require('web.dom_ready');
    var base = require("web_editor.base");
    var ajax = require('web.ajax');
    var utils = require('web.utils');
    var core = require('web.core');
    var config = require('web.config');
    require("website.content.zoomodoo");
    var _t = core._t;

    $('.engine').each(function () {
        var engine = this;
         $(engine).on('click', 'a.js_delete_product', function (ev) {
            ev.preventDefault();
            var $link = $(ev.currentTarget);
            var $input = $link.parent().find("input");
            var product_id = $input[0]['attributes']['data-product-id']['value'];
            var quote_id = $input[0]['attributes']['data-quote-id']['value'];
            var line_id = $input[0]['attributes']['data-line-id']['value']

             ajax.jsonRpc("/shop/engine/update_json", 'call', {
                    'quote_id':quote_id,
                    'line_id': line_id,
                    'product_id': product_id,
                    'set_qty': 0
                }).then(function (data) {
                     console.log("inside update_json");
                     console.log(data);
                     window.location.reload();
                });
            return false;
         });

         // hack to add and remove from cart with json
        $(engine).on('click', 'a.js_add_cart_json', function (ev) {
            ev.preventDefault();
            var $link = $(ev.currentTarget);
            var $input = $link.parent().find("input");
            var product_id = $input[0]['attributes']['data-product-id']['value'];
            var quote_id = $input[0]['attributes']['data-quote-id']['value'];
            var line_id = $input[0]['attributes']['data-line-id']['value'];
            ajax.jsonRpc("/shop/engine/count", 'call', {
                'quote_id':quote_id,
                'product_id': product_id
            }).then(function (maxCount) {
                 console.log("inside count");
                var min = parseFloat($input.data("min") || 0);
                var total_max_count = parseFloat($input[0]['attributes']['value']['value']) + parseFloat(maxCount);
                var max = parseFloat($input.data("max") || total_max_count);
                var quantity = ($link.has(".fa-minus").length ? -1 : 1) + parseFloat($input.val() || 0, 10);
                var new_qty = quantity > min ? (quantity < max ? quantity : max) : min;
                $('input[name="'+$input.attr("name")+'"]').add($input).filter(function () {
                    var $prod = $(this).closest('*:has(input[name="product_id"])');
                    return !$prod.length || +$prod.find('input[name="product_id"]').val() === product_id;
                }).val(new_qty).change();
                ajax.jsonRpc("/shop/engine/update_json", 'call', {
                    'quote_id':quote_id,
                    'line_id': line_id,
                    'product_id': product_id,
                    'set_qty': new_qty
                }).then(function (data) {
                     console.log("inside update_json");
                     console.log(data);
                     window.location.reload();
                });
            });
            return false;
        });
    });



});
