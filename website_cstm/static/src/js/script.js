odoo.define('WebsiteCstm.WebsiteCstm', function (require) {
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

    $(document).ready(function() {
        $('.search_autocomplete').devbridgeAutocomplete({
            serviceUrl: '/shop/get_suggest',
            onSelect: function (suggestion) {
                 window.location.replace(window.location.origin +
                    '/shop/product/' + suggestion.data.id + '?search=' + suggestion.value);
            }
        });
    });


     var ajax = require('web.ajax');

     var clickwatch = (function(){
              var timer = 0;
              return function(callback, ms){
                clearTimeout(timer);
                timer = setTimeout(callback, ms);
              };
    })();


    $('#notifyMe').on("click", function (event) {
    var self = $(this);
        clickwatch(function(){
            var inputEmailElm = $('input[name="notificationEmail"]')
            ajax.jsonRpc("/notifyme", 'call', {
                'product_id': inputEmailElm.data("productid"),
                'email': inputEmailElm.val()
            }).then(function (data) {
                if(!data)
                    $('.notifcationAlert').html("You have already subscribed for this product.")
                $('.notifcationGroup').hide();
                $('.notifcationAlert').show();
                console.log("data------------>",data);
            });
          }, 500);
      });

});