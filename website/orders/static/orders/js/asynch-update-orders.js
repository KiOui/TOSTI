
String.prototype.capitalize = function() {
    return this.charAt(0).toUpperCase() + this.slice(1);
};

function get_orders(data_url, csrf_token, callback_ok, callback_error, /*, args */) {
    let args = Array.prototype.slice.call(arguments, 4);
    jQuery(function($) {
        let data = {
            'csrfmiddlewaretoken': csrf_token,
        };
        $.ajax({type: 'POST', url: data_url, data, dataType:'json', asynch: true, success:
            function(data) {
                args.unshift(data.data);
                callback_ok.apply(this, args);
            }}).fail(function() {
                args.unshift("Error while getting order data.");
                callback_error.apply(this, args);
            });
        }
    )
}

function update_order_error(error, element) {

}

function update_order_data(orders, element) {
    let base = document.createElement('ol');
    base.classList.add('item-list');
    for (let i = 0; i < orders.length; i++) {
        let list_item_wrapper = create_element('li', ['pt-2', 'pb-2'], '');
        let list_item = create_element('div', ['item-list-div'], '');
        list_item_wrapper.appendChild(list_item);
        let username = create_element('p', ['item-username'], orders[i].user);
        let icon = create_element('i', ['fas', 'fa-'+orders[i].product.icon], '');

        list_item.appendChild(icon);
        list_item.appendChild(username);
        if (orders[i].own) {
            let user_icon = create_element('i', ['fas', 'fa-user'], '');
            list_item.appendChild(user_icon);
        }
        let status = null;
        if (orders[i].delivered && !orders[i].own) {
            status = create_element('div', ['bg-success', 'status-button', 'text-white'], 'Done');
        }
        else if (!orders[i].delivered && !orders[i].own) {
            status = create_element('div', ['bg-warning', 'status-button'], 'Processing');
        }
        else if (orders[i].delivered && orders[i].paid && orders[i].own) {
            status = create_element('div', ['bg-success', 'status-button', 'text-white'], 'Done');
        }
        else if (orders[i].delivered && !orders[i].paid && orders[i].own) {
            status = create_element('div', ['bg-warning', 'status-button', 'text-white'], 'Done');
        }
        else if (!orders[i].delivered && orders[i].paid && orders[i].own) {
            status = create_element('div', ['bg-warning', 'status-button'], 'Processing');
        }
        else {
            status = create_element('div', ['bg-danger', 'status-button'], 'Not payed');
        }
        list_item.append(status);
        base.appendChild(list_item_wrapper);
    }

    element.innerHTML = "";
    element.append(base);
}

function update_order(checkbox, order_id, property, callback_ok, callback_error /*, args */) {
    let args = Array.prototype.slice.call(arguments, 4);
    jQuery(function($) {
        let data = {
            'csrfmiddlewaretoken': CSRF_TOKEN,
            'order': order_id,
            'value': checkbox.classList.contains('btn-danger'),
            'property': property
        };
        $.ajax({type: 'POST', url: ORDER_UPDATE_URL, data, dataType:'json', asynch: true, success:
            function(data) {
                if (data.error) {
                    args.unshift(data.error);
                    callback_error.apply(this, args);
                }
                else {
                    args.unshift(checkbox);
                    args.unshift(data.value);
                    callback_ok.apply(this, args);
                }
            }}).fail(function() {
                args.unshift("Error while getting order data.");
                callback_error.apply(this, args);
            });
        }
    )
}

function update_checkbox_error(error) {
    ERROR_CONTAINER.innerHTML = error;
}

function update_checkbox(value, checkbox) {
    checkbox.classList.remove('btn-success');
    checkbox.classList.remove('btn-danger');
    if (value) {
        checkbox.classList.add('btn-success');
    }
    else {
        checkbox.classList.add('btn-danger');
    }
}

function update_orders(container, url, token) {
    get_orders(url, token, update_order_data, update_order_error, container);
    setTimeout(update_orders.bind(null, container, url, token), 5000);
}

$(document).ready(function() {
    if (typeof(ITEM_CONTAINER) !== 'undefined' &&
        typeof(ORDER_URL) !== 'undefined' &&
        typeof(CSRF_TOKEN) !== 'undefined') {
        update_orders(ITEM_CONTAINER, ORDER_URL, CSRF_TOKEN);
    }
    else {
        console.warn("One of the required javascript variables is not defined, automatic update is disabled.")
    }
});