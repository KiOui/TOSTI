
function get_ordered_data(data_url, csrf_token, callback_ok, callback_error, /*, args */) {
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
                    args.unshift(data.ordered_items);
                    callback_ok.apply(this, args);
                }
            }}).fail(function() {
                args.unshift("Error while getting order data.");
                callback_error.apply(this, args);
            });
        }
    )
}

function update_page_error(error) {
    ERROR_CONTAINER.innerHTML = error;
}

function construct_ordered_products_section(ordered_items) {
    let base = document.createElement('div');
    base.classList.add('product-list');
    for (let i = 0; i < ordered_items.length; i++) {
        let list_item = create_element('div', ['btn-ml', 'text-white'], '');
        let icon = create_element('i', ['fas', 'fa-' + ordered_items[i].product.icon], '');
        let name = create_element('h2', ['item-name'], ordered_items[i].product.name);

        list_item.appendChild(icon);
        list_item.appendChild(name);
        console.log(ordered_items[i]);
        if (!ordered_items[i].paid) {
            let status = create_element('p', ['item-status'], "payment needed");
            list_item.appendChild(status);
            list_item.classList.add('bg-danger');
        }
        else if (!ordered_items[i].delivered) {
            let status = create_element('p', ['item-status'], "paid");
            list_item.appendChild(status);
            list_item.classList.add('bg-warning');
        }
        else {
            let status = create_element('p', ['item-status'], "done");
            list_item.appendChild(status);
            list_item.classList.add('bg-success');
        }
        base.appendChild(list_item);
    }

    if (ordered_items.length === 0) {
        ORDER_CONTAINER.innerHTML = "<p class='alert-warning'>You have not ordered any items yet.</p>";
    }
    else {
        ORDER_CONTAINER.innerHTML = "";
        ORDER_CONTAINER.append(base);
    }
}

function update_orders() {
    get_ordered_data(UPDATE_URL, CSRF_TOKEN, construct_ordered_products_section, update_page_error);
    setTimeout(update_orders, 5000);
}

$(document).ready(function() {
    if (typeof(ORDER_CONTAINER) !== 'undefined' &&
        typeof(UPDATE_URL) !== 'undefined' &&
        typeof(CSRF_TOKEN) !== 'undefined' &&
        typeof(ERROR_CONTAINER) !== 'undefined') {
        update_orders();
    }
    else {
        console.warn("One of the required javascript variables is not defined, automatic update is disabled.")
    }
});