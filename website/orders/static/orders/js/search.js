
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
            }}).fail(function() {
                args.unshift("Error while adding product.");
                callback_error.apply(this, args);
            });
        }
    )
}

function add_product_success(successmsg) {
    SUCCESS_CONTAINER.innerHTML = successmsg;
    SUCCESS_CONTAINER.style.display = "";
    if (typeof(update_update_list) !== "undefined") {
        update_update_list();
    }
    $(POPUP_MODAL).modal('hide');
    SEARCH_BOX.value = "";
    SEARCH_RESULTS.style.display = "none";
}

function add_product_error(errormsg) {

}

function search_string() {
    let inputted = SEARCH_BOX.value;
    query_string(SEARCH_URL, search_success, search_error, inputted);
}

function query_string(data_url, callback_ok, callback_error, search /*, args */) {
    let args = Array.prototype.slice.call(arguments, 4);
    jQuery(function($) {
        let data = {
            'csrfmiddlewaretoken': get_csrf_token(),
            'query': search,
        };
        $.ajax({type: 'POST', url: data_url, data, dataType:'json', asynch: true, success:
            function(data) {
                if (data.error) {
                    args.unshift(data.errormsg);
                    callback_error.apply(args);
                }
                else {
                    args.unshift(data.data);
                    callback_ok.apply(this, args);
                }
            }}).fail(function() {
                args.unshift("Error while getting product data.");
                callback_error.apply(this, args);
            });
        }
    )
}

function search_success(products) {
    SEARCH_RESULTS.innerHTML = products;
    SEARCH_RESULTS.style.display = "";
}

function search_error(errormsg) {

}

jQuery(document).ready(function($) {
	SEARCH_BOX.addEventListener('keyup', () => {
	    clearTimeout(typingTimer);
	    let inputted = SEARCH_BOX.value;
	    if (inputted === "") {
    		SEARCH_RESULTS.style.display = "none";
	    }
	    else {
	    	SEARCH_RESULTS.style.display = "";
	    }

	    if (SEARCH_BOX.value) {
	        typingTimer = setTimeout(search_string, typingInterval);
	    }
	});
});