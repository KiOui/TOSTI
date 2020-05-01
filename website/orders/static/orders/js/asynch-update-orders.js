
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

function create_element(tag_name, class_list, text) {
    let element = document.createElement(tag_name);
    for (let i = 0; i < class_list.length; i++) {
        element.classList.add(class_list[i]);
    }
    element.appendChild(document.createTextNode(text));
    return element;
}

function create_checkbox(value, order_id, property) {
    let element = document.createElement('input');
    element.type = 'checkbox';
    element.setAttribute('onchange',"update_order(this, '" + order_id + "', '" + property + "', update_checkbox, update_checkbox_error)");
    if (value) {
        element.setAttribute('checked', value);
    }
    return element;
}

function update_order_data(orders, element) {
    let base = document.createElement('ul');
    base.classList.add('item-list');
    for (let i = 0; i < orders.length; i++) {
        let list_item = document.createElement('li');
        let username = create_element('p', ['item-username'], orders[i].user);
        let icon = create_element('i', ['fas', 'fa-'+orders[i].product.icon], '');
        let item_name = create_element('p', ['item-name'], orders[i].product.name);
        let item_price = create_element('p', ['item-price'], '€'+orders[i].price);
        let paid = create_checkbox(orders[i].paid, orders[i].id, 'paid');
        let delivered = create_checkbox(orders[i].delivered, orders[i].id, 'delivered');

        list_item.appendChild(username);
        list_item.appendChild(icon);
        list_item.appendChild(item_name);
        list_item.append(item_price);
        list_item.append(paid);
        list_item.append(delivered);
        base.appendChild(list_item);
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
            'value': checkbox.checked,
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
    checkbox.checked = value;
}

function update_orders(container, url, token) {
    get_orders(url, token, update_order_data, update_order_error, container);
    //setTimeout(update_orders.bind(null, container, url, token), 5000);
}

$(document).ready(function() {
    if (ITEM_CONTAINER && ORDER_URL && CSRF_TOKEN) {
        update_orders(ITEM_CONTAINER, ORDER_URL, CSRF_TOKEN);
    }
});