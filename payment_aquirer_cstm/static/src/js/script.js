odoo.define('payment_aquirer_cstm/static/src/js/script.js', function (require) {
'use strict';

    require('web.dom_ready');
    var ajax = require('web.ajax');
    var core = require('web.core');
    var _t = core._t;
    //var $carrier_badge = $('#delivery_carrier input[name="delivery_type"][value=3] ~ .badge:not(.o_delivery_compute)');
    var $carrierBadge = $('#delivery_carrier input[name="delivery_type"][value=3] ~ .o_wsale_delivery_badge_price');
    //var $compute_badge = $('#delivery_carrier input[name="delivery_type"][value=3] ~ .o_delivery_compute');
    var salesTeamMessage = $('textarea[name="sales_team_message"]');
    var $payButton = $('#o_payment_form_pay');
    var concurrency = require('web.concurrency');
    var dp = new concurrency.DropPrevious();

    var _handleCarrierUpdateResults = function(result) {
//        _handleCarrierUpdateResultBadge(result);
        var $payButton = $('#o_payment_form_pay');
        var $amountDelivery = $('#order_delivery .monetary_field');
        var $amountUntaxed = $('#order_total_untaxed .monetary_field');
        var $amountTax = $('#order_total_taxes .monetary_field');
        var $amountTotal = $('#order_total .monetary_field, #amount_total_summary.monetary_field');

        if (result.status === true) {
            $amountDelivery.html(result.new_amount_delivery);
            $amountUntaxed.html(result.new_amount_untaxed);
            $amountTax.html(result.new_amount_tax);
            $amountTotal.html(result.new_amount_total);
            var disabledReasons = $payButton.data('disabled_reasons') || {};
            disabledReasons.carrier_selection = false;
            $payButton.data('disabled_reasons', disabledReasons);
            $payButton.prop('disabled', _.contains($payButton.data('disabled_reasons'), true));
        } else {
            $amountDelivery.html(result.new_amount_delivery);
            $amountUntaxed.html(result.new_amount_untaxed);
            $amountTax.html(result.new_amount_tax);
            $amountTotal.html(result.new_amount_total);
        }
    };

    /**
     * @private
     * @param {Object} result
     */
    /*var _handleCarrierUpdateResultBadge = function (result) {
        var $carrierBadge = $('#delivery_carrier input[name="delivery_type"][value=' + result.carrier_id + '] ~ .o_wsale_delivery_badge_price');

        if (result.status === true) {
             // if free delivery (`free_over` field), show 'Free', not '$0'
             if (result.is_free_delivery) {
                 $carrierBadge.text(_t('Free'));
             } else {
                 $carrierBadge.html(result.new_amount_delivery);
             }
             $carrierBadge.removeClass('o_wsale_delivery_carrier_error');
        } else {
            $carrierBadge.addClass('o_wsale_delivery_carrier_error');
            $carrierBadge.text(result.error_message);
        }
    };*/

    $(document).ready(function() {
        ajax.jsonRpc("/checkHavingCarrierWithAccountNo", 'call', {
            }).then(function(data) {
                var carrier_acc_no = data['carrier_acc_no']
                console.log(carrier_acc_no);
                if (carrier_acc_no) {
                    console.log('In if ***');
                    $("#my_shipper_account_radio").prop('checked', true);
                    $("#my_shipper_account").prop('checked', true);
                    $("#expedited_shipping_div").parent().show();
                    $("#choose_a_delivery_method_label").parent().hide();
                    $("#delivery_method_custom").parent().hide();
                    $payButton.prop('disabled', false);
                    setTimeout(function(){
                        $payButton.prop('disabled', false);
                        console.log("delay done")
                        },3000);
                } else {
                    console.log('In else ***');
                    $("#shipping_options").children().hide();
                    $("#my_shipper_account").prop('checked', false);
                    $("#fedex_ground").prop('checked', true);
                    $("#expedited_shipping_div").parent().hide();
                    $("#my_shipper_account").parent().hide();
                    console.log('Error message');
                    console.log(data['error_message']);
                    console.log(data['new_amount_delivery']);
                    console.log(data['status']);

                    if (data['status'] === true){
                        console.log('in if blog');
                        $carrierBadge.html(data['new_amount_delivery']);
                        $carrierBadge.removeClass('o_wsale_delivery_carrier_error');
                        $payButton.prop('disabled', false);
                    }else{
                        console.log('in else blog');
                        $carrierBadge.addClass('o_wsale_delivery_carrier_error');
                        $carrierBadge.text(data['error_message']);
                        console.log(data['gen_pay_link']);
                        if (data['gen_pay_link'] == true) {
                        console.log('in gen pay true');
                        $payButton.prop('disabled', false);
                        setTimeout(function(){
                        $payButton.prop('disabled', false);
                        console.log("delay done")
                        },5000);
                        }
                        else{
                        console.log('in gen pay false');
                        $payButton.prop('disabled', true);
                        }

                        var disabledReasons = $payButton.data('disabled_reasons') || {};
                        disabledReasons.carrier_selection = true;
                        $payButton.data('disabled_reasons', disabledReasons);
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
               console.log('In my shipper radio 132');
               $payButton.prop('disabled', false);

               ajax.jsonRpc("/shop/get_carrier", 'call', {
                    'delivery_carrier_code': 'my_shipper_account'
               }).then(function(data) {
                    var carrier_id = parseInt(data['carrier_id'])
                    var values = {'carrier_id': carrier_id};
                    dp.add(ajax.jsonRpc('/shop/update_carrier', 'call', values))
                    .then(_handleCarrierUpdateResults);

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
                console.log('In charge_me_for_shipping_radio  161');
                //$payButton.prop('disabled', true);
//                var disabledReasons = $payButton.data('disabled_reasons') || {};
//                disabledReasons.carrier_selection = true;
//                $payButton.data('disabled_reasons', disabledReasons);

                ajax.jsonRpc("/shop/get_carrier", 'call', {
                    'delivery_carrier_code': 'fedex_ground'
                }).then(function(data) {
                    var carrier_id = parseInt(data['carrier_id'])
                    var values = {'carrier_id': carrier_id};
                    dp.add(ajax.jsonRpc('/shop/update_carrier', 'call', values))
                    .then(_handleCarrierUpdateResults);

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
                ajax.jsonRpc("/shop/get_carrier", 'call', {
                    'delivery_carrier_code': 'my_shipper_account'
                }).then(function(data) {
                    var carrier_id = parseInt(data['carrier_id'])
                    var values = {'carrier_id': carrier_id};
                    dp.add(ajax.jsonRpc('/shop/update_carrier', 'call', values))
                    .then(_handleCarrierUpdateResults);

               });
            }
        });

        $("#fedex_ground").change(function() {
            if ( $(this).is(':checked') ) {
                $("#expedited_shipping_div").parent().hide();
                ajax.jsonRpc("/shop/cart/expeditedShipping", 'call', {
                    'expedited_shipping': ""
                });
                ajax.jsonRpc("/shop/get_carrier", 'call', {
                    'delivery_carrier_code': 'fedex_ground'
                }).then(function(data) {
                    var carrier_id = parseInt(data['carrier_id'])
                    var values = {'carrier_id': carrier_id};
                    dp.add(ajax.jsonRpc('/shop/update_carrier', 'call', values))
                    .then(_handleCarrierUpdateResults);

               });
            }
        });

        $("#fedex_first_overnight_u_s_by_8_30_a_m_next_business_day_").change(function() {
            if ( $(this).is(':checked') ) {
                $("#expedited_shipping_div").parent().hide();
                ajax.jsonRpc("/shop/cart/expeditedShipping", 'call', {
                    'expedited_shipping': ""
                });
                ajax.jsonRpc("/shop/get_carrier", 'call', {
                    'delivery_carrier_code': 'fedex_first_overnight_u_s_by_8_30_a_m_next_business_day_'
                }).then(function(data) {
                    var carrier_id = parseInt(data['carrier_id'])
                    var values = {'carrier_id': carrier_id};
                    dp.add(ajax.jsonRpc('/shop/update_carrier', 'call', values))
                    .then(_handleCarrierUpdateResults);

               });
            }
        });

        $("#fedex_priority_overnight_u_s_by_10_30_a_m_next_business_day_").change(function() {
            if ( $(this).is(':checked') ) {
                $("#expedited_shipping_div").parent().hide();
                ajax.jsonRpc("/shop/cart/expeditedShipping", 'call', {
                    'expedited_shipping': ""
                });
                ajax.jsonRpc("/shop/get_carrier", 'call', {
                    'delivery_carrier_code': 'fedex_priority_overnight_u_s_by_10_30_a_m_next_business_day_'
                }).then(function(data) {
                    var carrier_id = parseInt(data['carrier_id'])
                    var values = {'carrier_id': carrier_id};
                    dp.add(ajax.jsonRpc('/shop/update_carrier', 'call', values))
                    .then(_handleCarrierUpdateResults);

               });
            }
        });

        $("#fedex_standard_overnight_u_s_by_3_p_m_next_business_day_").change(function() {
            if ( $(this).is(':checked') ) {
                $("#expedited_shipping_div").parent().hide();
                ajax.jsonRpc("/shop/cart/expeditedShipping", 'call', {
                    'expedited_shipping': ""
                });
                ajax.jsonRpc("/shop/get_carrier", 'call', {
                    'delivery_carrier_code': 'fedex_standard_overnight_u_s_by_3_p_m_next_business_day_'
                }).then(function(data) {
                    var carrier_id = parseInt(data['carrier_id'])
                    var values = {'carrier_id': carrier_id};
                    dp.add(ajax.jsonRpc('/shop/update_carrier', 'call', values))
                    .then(_handleCarrierUpdateResults);

               });
            }
        });

        $("#fedex_2nd_day_a_m_u_s_by_10_30_a_m_or_noon_second_business_day_").change(function() {
            if ( $(this).is(':checked') ) {
                $("#expedited_shipping_div").parent().hide();
                ajax.jsonRpc("/shop/cart/expeditedShipping", 'call', {
                    'expedited_shipping': ""
                });
                ajax.jsonRpc("/shop/get_carrier", 'call', {
                    'delivery_carrier_code': 'fedex_2nd_day_a_m_u_s_by_10_30_a_m_or_noon_second_business_day_'
                }).then(function(data) {
                    var carrier_id = parseInt(data['carrier_id'])
                    var values = {'carrier_id': carrier_id};
                    dp.add(ajax.jsonRpc('/shop/update_carrier', 'call', values))
                    .then(_handleCarrierUpdateResults);

               });
            }
        });

        $("#fedex_2nd_day_u_s_by_4_30_p_m_second_business_day_").change(function() {
            if ( $(this).is(':checked') ) {
                $("#expedited_shipping_div").parent().hide();
                ajax.jsonRpc("/shop/cart/expeditedShipping", 'call', {
                    'expedited_shipping': ""
                });
                ajax.jsonRpc("/shop/get_carrier", 'call', {
                    'delivery_carrier_code': 'fedex_2nd_day_u_s_by_4_30_p_m_second_business_day_'
                }).then(function(data) {
                    var carrier_id = parseInt(data['carrier_id'])
                    var values = {'carrier_id': carrier_id};
                    dp.add(ajax.jsonRpc('/shop/update_carrier', 'call', values))
                    .then(_handleCarrierUpdateResults);

               });
            }
        });

        $("#fedex_express_saver_u_s_by_4_30_p_m_third_business_day_").change(function() {
            if ( $(this).is(':checked') ) {
                $("#expedited_shipping_div").parent().hide();
                ajax.jsonRpc("/shop/cart/expeditedShipping", 'call', {
                    'expedited_shipping': ""
                });
                ajax.jsonRpc("/shop/get_carrier", 'call', {
                    'delivery_carrier_code': 'fedex_express_saver_u_s_by_4_30_p_m_third_business_day_'
                }).then(function(data) {
                    var carrier_id = parseInt(data['carrier_id'])
                    var values = {'carrier_id': carrier_id};
                    dp.add(ajax.jsonRpc('/shop/update_carrier', 'call', values))
                    .then(_handleCarrierUpdateResults);

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

        $("#po_submit").click(function(ev) {
          var $button = $(ev.currentTarget).closest('[type="submit"]');
          var $form = $(ev.currentTarget).closest('form');
          $button.attr('disabled', true);
          $form.submit();
        });

    });


    salesTeamMessage.on("change", function(event) {
        ajax.jsonRpc("/salesTeamMessage", 'call', {
            'sales_team_message': salesTeamMessage.val()
        });
    });
});