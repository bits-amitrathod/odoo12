odoo.define('WebsiteCstm.WebsiteCstm', function(require) {
    "use strict";

    const {Markup} = require('web.utils');
    const field_utils = require('web.field_utils');
    var VariantMixin = require('sale.VariantMixin');
    var publicWidget = require('web.public.widget');
    var core = require('web.core');
    var QWeb = core.qweb;
    require('web.dom_ready');

    var publicWidget = require('web.public.widget');
    var VariantMixin = require('sale.VariantMixin');

    VariantMixin._onChangeCombinationStock = function (ev, $parent, combination) {
            let product_id = 0;
            // needed for list view of variants
            if ($parent.find('input.product_id:checked').length) {
                product_id = $parent.find('input.product_id:checked').val();
            } else {
                product_id = $parent.find('.product_id').val();
            }
            const isMainProduct = combination.product_id &&
                ($parent.is('.js_main_product') || $parent.is('.main_product')) &&
                combination.product_id === parseInt(product_id);

            if (!this.isWebsite || !isMainProduct) {
                return;
            }

            const $addQtyInput = $parent.find('input[name="add_qty"]');
            let qty = $addQtyInput.val();
            let ctaWrapper = $parent[0].querySelector('#o_wsale_cta_wrapper');
            ctaWrapper.classList.replace('d-none', 'd-flex');
            ctaWrapper.classList.remove('out_of_stock');

            if (combination.product_type === 'product' && !combination.allow_out_of_stock_order) {
                combination.free_qty -= parseInt(combination.cart_qty);
                $addQtyInput.data('max', combination.free_qty || 1);
                if (combination.free_qty < 0) {
                    combination.free_qty = 0;
                }
                if (qty > combination.free_qty) {
                    qty = combination.free_qty || 1;
                    $addQtyInput.val(qty);
                }
                if (combination.free_qty < 1) {
         // ......................below line commented by bits..........................
        //            ctaWrapper.classList.replace('d-flex', 'd-none');

                    ctaWrapper.classList.add('out_of_stock');
                }
            }

            // needed xml-side for formatting of remaining qty
            combination.formatQuantity = (qty) => {
                if (Number.isInteger(qty)) {
                    return qty;
                } else {
                    const decimals = Math.max(
                        0,
                        Math.ceil(-Math.log10(combination.uom_rounding))
                    );
                    return field_utils.format.float(qty, {digits: [false, decimals]});
                }
            }

            $('.oe_website_sale')
                .find('.availability_message_' + combination.product_template)
                .remove();
            combination.has_out_of_stock_message = $(combination.out_of_stock_message).text() !== '';
            combination.out_of_stock_message = Markup(combination.out_of_stock_message);
            const $message = $(QWeb.render(
                'website_sale_stock.product_availability',
                combination
            ));
        //    ...................below comment added by bits ...................
            if (!(combination.free_qty >= 0  && !combination.cart_qty)){
             $('div.availability_messages').html($message);
            }

    };


    $(document).ready(function() {
        $("[rel='tooltip']").tooltip();

        $('.thumbnail').hover(
            function() {
                $(this).find('.caption').fadeIn(250)
            },
            function() {
                $(this).find('.caption').fadeOut(205)
            }
        );
    });

//    $(document).ready(function() {
//        $('.search_autocomplete').devbridgeAutocomplete({
//            appendTo: $('.o_website_sale_search'),
//            serviceUrl: '/shop/get_suggest',
//            onSelect: function(suggestion) {
//                window.location.replace(window.location.origin +
//                    '/shop/product/' + suggestion.data.id + '?search=' + suggestion.value);
//            }
//        });
//    });


    var ajax = require('web.ajax');

    var clickwatch = (function() {
        var timer = 0;
        return function(callback, ms) {
            clearTimeout(timer);
            timer = setTimeout(callback, ms);
        };
    })();

    var inputEmailElm = $('input[name="notificationEmail"]');
    var invalidEmail = $('.invalidEmail');

    function validateEmail(email) {
        var re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
        return re.test(String(email).toLowerCase());
    }

    inputEmailElm.on("change", function(event) {
        if (validateEmail(event.currentTarget.value)) {
            invalidEmail.hide();
        } else {
            invalidEmail.show();
        }

    });
    $('#notifyMe').on("click", function(event) {
        var email = inputEmailElm.val();
        if (!validateEmail(email)) {
            invalidEmail.show();
            return
        }
        clickwatch(function() {
            ajax.jsonRpc("/notifyme", 'call', {
                'product_id': inputEmailElm.data("productid"),
                'email': email
            }).then(function(data) {
                if (!data)
                    $('.notifcationAlert').html("You have already subscribed for this product.")
                $('.notifcationGroup').hide();
                $('.notifcationAlert').show();
            });
        }, 500);
    });

});