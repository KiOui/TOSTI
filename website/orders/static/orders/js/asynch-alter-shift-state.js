
function send_post_toggle(data_url, csrf_token, callback_ok, callback_error, active/*, args */) {
    let args = Array.prototype.slice.call(arguments, 5);
    jQuery(function($) {
        let data = {
            'csrfmiddlewaretoken': csrf_token,
            'active': active
        };
        $.ajax({type: 'POST', url: data_url, data, dataType:'json', asynch: true, success:
            function(data) {
                if (data.error) {
                    args.unshift(data.error);
                    callback_error.apply(args);
                }
                else {
                    args.unshift(data);
                    callback_ok.apply(this, args);
                }
            }}).fail(function() {
                args.unshift("Error while getting order data.");
                callback_error.apply(this, args);
            });
        }
    )
}

function send_post(data_url, csrf_token, callback_ok, callback_error/*, args */) {
    let args = Array.prototype.slice.call(arguments, 4);
    jQuery(function($) {
        let data = {
            'csrfmiddlewaretoken': csrf_token,
        };
        $.ajax({type: 'POST', url: data_url, data, dataType:'json', asynch: true, success:
            function(data) {
                if (data.error) {
                    args.unshift(data.error);
                    callback_error.apply(args);
                }
                else {
                    args.unshift(data);
                    callback_ok.apply(this, args);
                }
            }}).fail(function() {
                args.unshift("Error while getting order data.");
                callback_error.apply(this, args);
            });
        }
    )
}

function update_toggle(data, element) {
    if (data.active) {
        element.classList.remove(['bg-danger']);
        element.classList.add('bg-success');
    }
    else {
        element.classList.remove(['bg-success']);
        element.classList.add('bg-danger');
    }
}

function display_error(error) {
    SUCCESS_CONTAINER.style.display = "none";
    ERROR_CONTAINER.innerHTML = error;
    ERROR_CONTAINER.style.display = "";
}

function toggle_shift_activation(element) {
    send_post_toggle(TOGGLE_SHIFT_URL, CSRF_TOKEN, update_toggle, display_error, element.classList.contains('bg-danger'), element);
}

function add_time() {
    send_post(ADD_TIME_URL, CSRF_TOKEN, succeeded_add_time, display_error);
}

function add_capacity() {
    send_post(ADD_CAPACITY_URL, CSRF_TOKEN, succeeded_add_capacity, display_error);
}

function succeeded_add_time() {
    ERROR_CONTAINER.style.display = "none";
    SUCCESS_CONTAINER.innerHTML = "Added 5 minutes to the end time of this shift";
    SUCCESS_CONTAINER.style.display = "";
}

function succeeded_add_capacity() {
    ERROR_CONTAINER.style.display = "none";
    SUCCESS_CONTAINER.innerHTML = "Added 5 capacity to this shift";
    SUCCESS_CONTAINER.style.display = "";
}

$(document).ready(function() {
    if (typeof(SUCCESS_CONTAINER) !== 'undefined' &&
        typeof(CSRF_TOKEN) !== 'undefined' &&
        typeof(ERROR_CONTAINER) !== 'undefined' &&
        typeof(TOGGLE_SHIFT_URL) !== 'undefined' &&
        typeof(ADD_TIME_URL) !== 'undefined' &&
        typeof(ADD_CAPACITY_URL) !== 'undefined') {

    }
    else {
        console.warn("One of the required javascript variables is not defined, footer buttons are disabled.")
    }
});