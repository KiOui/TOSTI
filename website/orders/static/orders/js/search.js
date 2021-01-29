
let typingTimer;
let typingInterval = 200;

function add_product(data_url, callback_ok, callback_error, product_id) {
    let args = Array.prototype.slice.call(arguments, 4);
    jQuery(function($) {
        let data = {
            'csrfmiddlewaretoken': get_csrf_token(),
            'product': product_id,
        };
        $.ajax({type: 'POST', url: data_url, data, dataType:'json', asynch: true, success:
            function(data) {
                if (data.error) {
                    args.unshift(data.errormsg);
                    callback_error.apply(args);
                }
                else {
                    args.unshift(data.successmsg);
                    callback_ok.apply(this, args);
                }
            }}).fail(function(jqXHR, textStatus, errorThrown) {
                callback_error.apply(this, args);
            });
        }
    )
}

function order_added(data) {
    if (typeof(update_update_list) !== "undefined") {
        update_update_list();
    }
    $(POPUP_MODAL).modal('hide');
    scanner_vue.search_results = [];
    scanner_vue.search_input = "";
    toastr.success("Order added to queue.")
}

function order_added_error(error_data) {
    if (error_data.detail) {
        toastr.error("The following error(s) occurred: ".concat(error_data.detail), "Failed to add product");
    }
    else {
        toastr.error("Failed to add product.")
    }
}

function search_string() {
    query_string(SEARCH_URL, search_success, search_error, scanner_vue.search_input);
}

function query_string(data_url, callback_ok, callback_error, search /*, args */) {
    let args = Array.prototype.slice.call(arguments, 4);
    jQuery(function($) {
        let headers = {
            "X-CSRFToken": get_csrf_token(),
        };
        let data = {
            "query": search
        }
        $.ajax({type: 'GET', url: data_url, data, asynch: true, headers: headers, success:
            function(data) {
                args.unshift(data);
                callback_ok.apply(this, args);
            }}).fail(function() {
                args.unshift("Error while getting product data.");
                callback_error.apply(this, args);
            });
        }
    )
}

function set_search_timeout() {
    clearTimeout(typingTimer);
    if (scanner_vue.search_input !== "") {
        typingTimer = setTimeout(search_string, typingInterval);
    }
}

function search_success(products) {
    scanner_vue.search_results = products;
}

function search_error(errormsg) {

}