
let MAX_ORDERS = 5;
let PRODUCTS = [];

String.prototype.capitalize = function() {
    return this.charAt(0).toUpperCase() + this.slice(1);
};

function get_list(data_url, csrf_token, callback_ok, callback_error, /*, args */) {
    let args = Array.prototype.slice.call(arguments, 4);
    jQuery(function($) {
        let data = {
            'csrfmiddlewaretoken': csrf_token,
            'option': "list"
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

function update_page_error(error) {
    ERROR_CONTAINER.innerHTML = error;
    ERROR_CONTAINER.style.display = "block";
}

function get_amount_of_item_orders(product_id) {
    let amount_of_items = 0;
    let cart = get_cart_list();
    for (let i = 0; i < cart.length; i++) {
        if (cart[i] === product_id) {
            amount_of_items += 1;
        }
    }
    return amount_of_items;
}

function update_page_data(data) {
    MAX_ORDERS = data.shift_max;
    PRODUCTS = data.products;
    refresh();
}

function construct_products_section(products) {
    let base = document.createElement('ul');
    base.classList.add('order-list');
    for (let i = 0; i < products.length; i++) {
        let list_item = create_element('li', ['order-item', 'pt-2', 'pb-2', 'mt-2', 'mb-2'], '');
        let icon = create_element('i', ['fas', 'fa-'+products[i].icon], '');
        let name = create_element('p', ['order-name'], products[i].name);
        let button = create_element('input', ['btn', 'btn-success', 'ml-2'], "");
        button.type = 'button';
        button.value = "Add";
        button.setAttribute('onclick', "add_product(" + products[i].id + ")");
        let price = create_element('p', ['item-price'], '€' + products[i].price);

        list_item.appendChild(icon);
        list_item.appendChild(name);
        list_item.appendChild(price);
        list_item.appendChild(button);
        if (products[i].max_allowed !== null && get_amount_of_item_orders(products[i].id) >= products[i].max_allowed) {
            let overlay = create_element('div', ['item-overlay'], "");
            let overlay_text = create_element('p', ['alert', 'alert-warning'], "You have ordered the maximum of this item.");
            overlay.appendChild(overlay_text);
            list_item.appendChild(overlay);
        }
        base.appendChild(list_item);
    }

    if (products.length === 0) {
        return "<p class='alert alert-warning'>There are no products you can order.</p>";
    }

    return base;
}

function create_maximum_ordered_overlay(element) {
    let overlay = create_element('div', ['item-overlay'], "");
    let overlay_text = create_element('p', ['alert', 'alert-warning'], "You have ordered the maximum amount of orders you can place this shift.");
    overlay.appendChild(overlay_text);
    element.append(overlay);
}

function construct_order_section() {
    let base = document.createElement('ul');
    base.classList.add('order-list');
    let cart = get_cart_list();
    for (let i = 0; i < cart.length; i++) {
        let product = find_product_details(cart[i]);
        if (product !== null) {
            let list_item = create_element('li', ['order-item'], '');
            let icon = create_element('i', ['fas', 'fa-' + product.icon], '');
            let name = create_element('p', ['order-name'], product.name);
            let button = create_element('input', ['btn', 'btn-danger', 'ml-2'], "");
            button.type = 'button';
            button.value = "Remove";
            button.setAttribute('onclick', "delete_product(" + product.id + ")");

            list_item.appendChild(icon);
            list_item.appendChild(name);
            list_item.appendChild(button);
            base.appendChild(list_item);
        }
    }

    if (cart.length === 0) {
        ORDER_CONTAINER.innerHTML = "<p class='alert alert-warning'>There are no items in your cart.</p>";
    }
    else {
        ORDER_CONTAINER.innerHTML = "";
        ORDER_CONTAINER.append(base);
    }
}

function delete_product(product_id) {
    let cart = get_cart_list();
    for (let i = 0; i < cart.length; i++) {
        if (cart[i] === product_id) {
            cart.splice(i, 1);
            set_cart_list(cart);
            refresh();
            return;
        }
    }
}

function find_product_details(product_id) {
    for (let i = 0; i < PRODUCTS.length; i++) {
        if (PRODUCTS[i].id === product_id) {
            return PRODUCTS[i];
        }
    }
    return null;
}

function get_amount_of_cart_items() {
    let cart = get_cart_list();
    return cart.length;
}

function get_amount_of_restricted_cart_items() {
    let cart = get_cart_list();
    return cart.filter(
        function(value, index, arr)
        {
            let product_details = find_product_details(value);
            return product_details !== null && !product_details.ignore_shift_restriction;
    }).length;
}

function add_product(product_id) {
    let product_details = find_product_details(product_id);
    if (product_details !== null && (get_amount_of_restricted_cart_items() < MAX_ORDERS || product_details.ignore_shift_restriction)) {
        let cart = get_cart_list();
        cart.push(product_id);
        set_cart_list(cart);
        refresh();
        return true;
    }
    else {
        return false;
    }
}

function get_cart_list() {
	let cookie = get_cookie(CART_COOKIE_NAME);
	try {
		let list = JSON.parse(cookie);
		if (list === null) {
		    return [];
        }
        else {
            return list;
        }
	}
	catch(error) {
		return [];
	}
}

function set_cart_list(list) {
    if (!set_list_cookie(CART_COOKIE_NAME, list, 1)) {
        console.error("Could not set list cookie");
        set_list_cookie(CART_COOKIE_NAME, [], 1);
    }
}

function get_restricted_products(products) {
    let ret = [];
    for (let i = 0; i < products.length; i++) {
        if (!products[i].ignore_shift_restriction) {
            ret.push(products[i]);
        }
    }
    return ret;
}

function get_unrestricted_products(products) {
    let ret = [];
    for (let i = 0; i < products.length; i++) {
        if (products[i].ignore_shift_restriction) {
            ret.push(products[i]);
        }
    }
    return ret;
}

function refresh() {
    let restricted_products = get_restricted_products(PRODUCTS);
    let unrestricted_products = get_unrestricted_products(PRODUCTS);
    let restricted_base = create_element('div', [], '');
    let unrestricted_base = create_element('div', [], '');
    if (restricted_products.length > 0) {
        let restricted_list = construct_products_section(restricted_products);
        if (MAX_ORDERS !== null && get_amount_of_restricted_cart_items() >= MAX_ORDERS) {
            let overlay = create_element('div', ['item-overlay'], "");
            let overlay_text = create_element('p', ['alert', 'alert-warning'], "You have ordered the maximum amount of orders you can place this shift.");
            overlay.appendChild(overlay_text);
            restricted_list.append(overlay);
        }
        restricted_base.append(restricted_list);
    }
    if (unrestricted_products.length > 0) {
        unrestricted_base.append(construct_products_section(unrestricted_products));
    }
    PRODUCT_CONTAINER.innerHTML = "";
    PRODUCT_CONTAINER.append(restricted_base);
    PRODUCT_CONTAINER.append(unrestricted_base);
    construct_order_section();
    display_order_button(get_cart_list().length > 0);
}

function display_order_button(display) {
    if (display) {
        ORDER_BUTTON.style.display = '';
    }
    else {
        ORDER_BUTTON.style.display = 'none';
    }
}

$(document).ready(function() {
    if (typeof(PRODUCT_CONTAINER) !== 'undefined' &&
        typeof(UPDATE_URL) !== 'undefined' &&
        typeof(CSRF_TOKEN) !== 'undefined' &&
        typeof(ERROR_CONTAINER) !== 'undefined' &&
        typeof(CART_COOKIE_NAME) !== 'undefined' &&
        typeof(ORDER_BUTTON) !== 'undefined') {
        if (get_cookie(CART_COOKIE_NAME) === null) {
            set_list_cookie(CART_COOKIE_NAME, [], 1);
        }
        get_list(UPDATE_URL, CSRF_TOKEN, update_page_data, update_page_error, PRODUCT_CONTAINER);
    }
    else {
        console.warn("One of the required javascript variables is not defined, automatic update is disabled.")
    }
});