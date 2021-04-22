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
                    $("#my_shipper_account").prop('checked', true);
                    $("#expedited_shipping_div").parent().show();
                    $("#choose_a_delivery_method_label").parent().hide();
                    $("#delivery_method_custom").parent().hide();
                } else {
                    $("#shipping_options").children().hide();
                    $("#my_shipper_account").prop('checked', false);
                    $("#fedex_ground").prop('checked', true);
                    $("#expedited_shipping_div").parent().hide();
                    $("#my_shipper_account").parent().hide();
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
               $("#my_shipper_account").prop('checked', true);
               $("#expedited_shipping_div").parent().show();
               $("#choose_a_delivery_method_label").parent().hide();
               $("#delivery_method_custom").parent().hide();
               var e = document.getElementById("selectDeliveryMethod");
               var value = e.options[e.selectedIndex].value;
               ajax.jsonRpc("/shop/cart/expeditedShipping", 'call', {
                   'expedited_shipping': value
               });

               $pay_button.prop('disabled', false);

               ajax.jsonRpc("/shop/get_carrier", 'call', {
                    'delivery_carrier_code': 'my_shipper_account'
               }).then(function(data) {
                    var carrier_id = int(data['carrier_id'])
                    var values = {'carrier_id': carrier_id};
                    dp.add(ajax.jsonRpc('/shop/update_carrier', 'call', values))
                    .then(_onCarrierUpdateAnswers);

               });

           }
        });


        $("#charge_me_for_shipping_radio").unbind().click(function(event) {
           if ( $(this).is(':checked') ) {
                event.stopPropagation();
                $("#choose_a_delivery_method_label").parent().show();
                $("#delivery_method_custom").parent().show();
                $("#my_shipper_account").prop('checked', false);
                $("#fedex_ground").prop('checked', true);
                $("#expedited_shipping_div").parent().hide();
                $("#my_shipper_account").parent().hide();
                ajax.jsonRpc("/shop/cart/expeditedShipping", 'call', {
                    'expedited_shipping': ""
                });

                $pay_button.data('disabled_reasons', $pay_button.data('disabled_reasons') || {});
                $pay_button.data('disabled_reasons').carrier_selection = true;
                $pay_button.prop('disabled', true);

                ajax.jsonRpc("/shop/get_carrier", 'call', {
                    'delivery_carrier_code': 'fedex_ground'
                }).then(function(data) {
                    var carrier_id = int(data['carrier_id'])
                    var values = {'carrier_id': carrier_id};
                    dp.add(ajax.jsonRpc('/shop/update_carrier', 'call', values))
                    .then(_onCarrierUpdateAnswers);

               });
           }
        });


        $("#my_shipper_account").change(function() {
            if ( $(this).is(':checked') ) {
                $("#expedited_shipping_div").parent().show();
                var e = document.getElementById("selectDeliveryMethod");
                var value = e.options[e.selectedIndex].value;
                ajax.jsonRpc("/shop/cart/expeditedShipping", 'call', {
                    'expedited_shipping': value
                });
            }
        });

        $("#fedex_ground").change(function() {
            if ( $(this).is(':checked') ) {
                $("#expedited_shipping_div").parent().hide();
                ajax.jsonRpc("/shop/cart/expeditedShipping", 'call', {
                    'expedited_shipping': ""
                });
            }
        });

        $("#fedex_first_overnight_u_s_by_8_30_a_m_next_business_day_").change(function() {
            if ( $(this).is(':checked') ) {
                $("#expedited_shipping_div").parent().hide();
                ajax.jsonRpc("/shop/cart/expeditedShipping", 'call', {
                    'expedited_shipping': ""
                });
            }
        });

        $("#fedex_priority_overnight_u_s_by_10_30_a_m_next_business_day_").change(function() {
            if ( $(this).is(':checked') ) {
                $("#expedited_shipping_div").parent().hide();
                ajax.jsonRpc("/shop/cart/expeditedShipping", 'call', {
                    'expedited_shipping': ""
                });
            }
        });

        $("#fedex_standard_overnight_u_s_by_3_p_m_next_business_day_").change(function() {
            if ( $(this).is(':checked') ) {
                $("#expedited_shipping_div").parent().hide();
                ajax.jsonRpc("/shop/cart/expeditedShipping", 'call', {
                    'expedited_shipping': ""
                });
            }
        });

        $("#fedex_2nd_day_a_m_u_s_by_10_30_a_m_or_noon_second_business_day_").change(function() {
            if ( $(this).is(':checked') ) {
                $("#expedited_shipping_div").parent().hide();
                ajax.jsonRpc("/shop/cart/expeditedShipping", 'call', {
                    'expedited_shipping': ""
                });
            }
        });

        $("#fedex_2nd_day_p_m_u_s_by_4_30_p_m_second_business_day_").change(function() {
            if ( $(this).is(':checked') ) {
                $("#expedited_shipping_div").parent().hide();
                ajax.jsonRpc("/shop/cart/expeditedShipping", 'call', {
                    'expedited_shipping': ""
                });
            }
        });

        $("#fedex_express_saver_u_s_by_4_30_p_m_third_business_day_").change(function() {
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