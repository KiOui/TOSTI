
function get_orders(data_url, csrf_token, callback, admin/*, args */) {
    let args = Array.prototype.slice.call(arguments, 4);
    jQuery(function ($) {
            let data = {
                'csrfmiddlewaretoken': csrf_token,
                'admin': admin
            };
            $.ajax({
                type: 'POST', url: data_url, data, dataType: 'json', asynch: true, success:
                    function (data) {
                        args.unshift(data);
                        callback.apply(this, args);
                    }
            }).fail(function () {
                console.error("Error while getting order data.");
            });
        }
    )
}

function update_order_data(orders) {
    ORDER_CONTAINER.innerHTML = orders.data;
}

function update_orders() {
    get_orders(ORDER_REFRESH_URL, ORDER_CSRF_TOKEN, update_order_data, ORDER_REFRESH_ADMIN);
}

function update_orders_continuous() {
    update_orders();
    setTimeout(update_orders_continuous, 5000);
}

$(document).ready(function() {
    if (typeof(ORDER_CONTAINER) !== 'undefined' &&
        typeof(ORDER_REFRESH_URL) !== 'undefined' &&
        typeof(ORDER_CSRF_TOKEN) !== 'undefined' &&
        typeof(ORDER_REFRESH_ADMIN) !== 'undefined') {
        update_orders_continuous();
    }
    else {
        console.warn("One of the required javascript variables is not defined, automatic update is disabled.")
    }
});