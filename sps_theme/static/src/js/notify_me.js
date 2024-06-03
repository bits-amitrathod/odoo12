odoo.define('WebsiteCstm.WebsiteCstm', function(require) {
    "use strict";
    require('web.dom_ready');
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