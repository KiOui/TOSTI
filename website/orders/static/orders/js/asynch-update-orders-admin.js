
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

function create_checkbox(value, order_id, property, class_list) {
    let element = document.createElement('input');
    element.type = 'button';
    element.value = property.capitalize();
    element.setAttribute('onclick',"update_order(this, '" + order_id + "', '" + property + "', update_checkbox, update_checkbox_error)");
    element.classList.add('btn');
    if (value) {
        element.classList.add('btn-success');
    }
    else {
        element.classList.add('btn-danger');
    }
    for (let i = 0; i < class_list.length; i++) {
        element.classList.add(class_list[i]);
    }
    return element;
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
        let paid = create_checkbox(orders[i].paid, orders[i].id, 'paid', ['checkbox-paid']);
        let delivered = create_checkbox(orders[i].delivered, orders[i].id, 'delivered', ['checkbox-delivered']);

        list_item.appendChild(icon);
        list_item.appendChild(username);
        list_item.append(paid);
        list_item.append(delivered);
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