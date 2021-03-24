odoo.define('payment_aquirer_cstm.payment_aquirer_cstm', function(require) {
    "use strict";
    require('web.dom_ready');
    var ajax = require('web.ajax');
    var core = require('web.core');
    var _t = core._t;
    var $carrier_badge = $('#delivery_carrier input[name="delivery_type"][value=3] ~ .badge:not(.o_delivery_compute)');
    var $compute_badge = $('#delivery_carrier input[name="delivery_type"][value=3] ~ .o_delivery_compute');
    var salesTeamMessage = $('textarea[name="sales_team_message"]');
    var $pay_button = $('#o_payment_form_pay');
    var concurrency = require('web.concurrency');
    var dp = new concurrency.DropPrevious();

    var _onCarrierUpdateAnswers = function(result) {
        var $amount_delivery = $('#order_delivery span.oe_currency_value');
        var $amount_untaxed = $('#order_total_untaxed span.oe_currency_value');
        var $amount_tax = $('#order_total_taxes span.oe_currency_value');
        var $amount_total = $('#order_total, #amount_total_summary').find('span.oe_currency_value');
        var $carrier_badge = $('#delivery_carrier input[name="delivery_type"][value=' + result.carrier_id + '] ~ .badge:not(.o_delivery_compute)');
        var $compute_badge = $('#delivery_carrier input[name="delivery_type"][value=' + result.carrier_id + '] ~ .o_delivery_compute');
        var $discount = $('#order_discounted');

        if ($discount && result.new_amount_order_discounted) {
            // Cross module without bridge
            // Update discount of the order
            $discount.find('.oe_currency_value').text(result.new_amount_order_discounted);

            // We are in freeshipping, so every carrier is Free
            $('#delivery_carrier .badge').text(_t('Free'));
        }

        if (result.status === true) {
            $amount_delivery.text(result.new_amount_delivery);
            $amount_untaxed.text(result.new_amount_untaxed);
            $amount_tax.text(result.new_amount_tax);
            $amount_total.text(result.new_amount_total);
            $carrier_badge.children('span').text(result.new_amount_delivery);
            $carrier_badge.removeClass('d-none');
            $compute_badge.addClass('d-none');
            $pay_button.data('disabled_reasons').carrier_selection = false;
            $pay_button.prop('disabled', _.contains($pay_button.data('disabled_reasons'), true));
        }
        else {
            console.error(result.error_message);
            $compute_badge.text(result.error_message);
            $amount_delivery.text(result.new_amount_delivery);
            $amount_untaxed.text(result.new_amount_untaxed);
            $amount_tax.text(result.new_amount_tax);
            $amount_total.text(result.new_amount_total);
        }
    };

    $(document).ready(function() {
        ajax.jsonRpc("/checkHavingCarrierWithAccountNo", 'call', {
            }).then(function(data) {
                var carrier_acc_no = data['carrier_acc_no']
                console.log(carrier_acc_no);
                if (carrier_acc_no) {
                    $("#my_shipper_account_radio").prop('checked', true);
                    $("#delivery_35").prop('checked', true);
                    $("#expedited_shipping_div").parent().show();
                    $("#choose_a_delivery_method_label").parent().hide();
                    $("#delivery_method_custom").parent().hide();
                } else {
                    $("#shipping_options").children().hide();
                    $("#delivery_35").prop('checked', false);
                    $("#delivery_3").prop('checked', true);
                    $("#expedited_shipping_div").parent().hide();
                    $("#delivery_35").parent().hide();
                    console.log('Error message');
                    console.log(data['error_message']);
                    console.log(data['amount_delivery']);
                    console.log(data['status']);
                    if (data['status'] === true){
                        console.log('in if blog');
                        $carrier_badge.children('span').text(data['amount_delivery']);
                        $carrier_badge.removeClass('d-none');
                        $compute_badge.addClass('d-none');
                    }else{
                        console.log('in else blog');
                        $carrier_badge.addClass('d-none');
                        $compute_badge.removeClass('d-none');
                        $compute_badge.text(data['error_message']);
                    }
                }
         });

         $("#my_shipper_account_radio").unbind().click(function() {
           if ( $(this).is(':checked') ) {
               $("#delivery_35").prop('checked', true);
               $("#expedited_shipping_div").parent().show();
               $("#choose_a_delivery_method_label").parent().hide();
               $("#delivery_method_custom").parent().hide();
               var e = document.getElementById("selectDeliveryMethod");
               var value = e.options[e.selectedIndex].value;
               ajax.jsonRpc("/shop/cart/expeditedShipping", 'call', {
                   'expedited_shipping': value
               });

               var carrier_id = 35
               var values = {'carrier_id': carrier_id};
               dp.add(ajax.jsonRpc('/shop/update_carrier', 'call', values))
                  .then(_onCarrierUpdateAnswers);
           }
        });


        $("#charge_me_for_shipping_radio").unbind().click(function(event) {
           if ( $(this).is(':checked') ) {
                event.stopPropagation();
                $("#choose_a_delivery_method_label").parent().show();
                $("#delivery_method_custom").parent().show();
                $("#delivery_35").prop('checked', false);
                $("#delivery_3").prop('checked', true);
                $("#expedited_shipping_div").parent().hide();
                $("#delivery_35").parent().hide();
                ajax.jsonRpc("/shop/cart/expeditedShipping", 'call', {
                    'expedited_shipping': ""
                });

                $pay_button.data('disabled_reasons', $pay_button.data('disabled_reasons') || {});
                $pay_button.data('disabled_reasons').carrier_selection = true;
                $pay_button.prop('disabled', true);
                var carrier_id = 3
                var values = {'carrier_id': carrier_id};
                dp.add(ajax.jsonRpc('/shop/update_carrier', 'call', values))
                  .then(_onCarrierUpdateAnswers);
           }
        });


        $("#delivery_35").change(function() {
            if ( $(this).is(':checked') ) {
                $("#expedited_shipping_div").parent().show();
                var e = document.getElementById("selectDeliveryMethod");
                var value = e.options[e.selectedIndex].value;
                ajax.jsonRpc("/shop/cart/expeditedShipping", 'call', {
                    'expedited_shipping': value
                });
            }
        });

        $("#delivery_3").change(function() {
            if ( $(this).is(':checked') ) {
                $("#expedited_shipping_div").parent().hide();
                ajax.jsonRpc("/shop/cart/expeditedShipping", 'call', {
                    'expedited_shipping': ""
                });
            }
        });

        $("#delivery_4").change(function() {
            if ( $(this).is(':checked') ) {
                $("#expedited_shipping_div").parent().hide();
                ajax.jsonRpc("/shop/cart/expeditedShipping", 'call', {
                    'expedited_shipping': ""
                });
            }
        });

        $("#delivery_5").change(function() {
            if ( $(this).is(':checked') ) {
                $("#expedited_shipping_div").parent().hide();
                ajax.jsonRpc("/shop/cart/expeditedShipping", 'call', {
                    'expedited_shipping': ""
                });
            }
        });

        $("#delivery_6").change(function() {
            if ( $(this).is(':checked') ) {
                $("#expedited_shipping_div").parent().hide();
                ajax.jsonRpc("/shop/cart/expeditedShipping", 'call', {
                    'expedited_shipping': ""
                });
            }
        });

        $("#delivery_7").change(function() {
            if ( $(this).is(':checked') ) {
                $("#expedited_shipping_div").parent().hide();
                ajax.jsonRpc("/shop/cart/expeditedShipping", 'call', {
                    'expedited_shipping': ""
                });
            }
        });

        $("#delivery_8").change(function() {
            if ( $(this).is(':checked') ) {
                $("#expedited_shipping_div").parent().hide();
                ajax.jsonRpc("/shop/cart/expeditedShipping", 'call', {
                    'expedited_shipping': ""
                });
            }
        });

        $("#delivery_16").change(function() {
            if ( $(this).is(':checked') ) {
                $("#expedited_shipping_div").parent().hide();
                ajax.jsonRpc("/shop/cart/expeditedShipping", 'call', {
                    'expedited_shipping': ""
                });
            }
        });

        $("#selectDeliveryMethod").unbind().change(function() {
            var e = document.getElementById("selectDeliveryMethod");
            var value = e.options[e.selectedIndex].value;
            console.log(value);
            ajax.jsonRpc("/shop/cart/expeditedShipping", 'call', {
                'expedited_shipping': value
            });
        });
    });


    salesTeamMessage.on("change", function(event) {
        ajax.jsonRpc("/salesTeamMessage", 'call', {
            'sales_team_message': salesTeamMessage.val()
        });
    });
});