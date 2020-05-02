
let MAX_ORDERS = 0;
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

function construct_products_section() {
    let base = document.createElement('div');
    base.classList.add('product-list');
    for (let i = 0; i < PRODUCTS.length; i++) {
        let list_item = create_element('div', ['btn-ml'], '');
        let icon = create_element('i', ['fas', 'fa-'+PRODUCTS[i].icon], '');
        let name = create_element('h2', ['item-name'], 'Add ' + PRODUCTS[i].name);

        list_item.appendChild(icon);
        list_item.appendChild(name);
        console.log(get_amount_of_item_orders(PRODUCTS[i].id));
        if ((MAX_ORDERS === null || get_amount_of_cart_items() < MAX_ORDERS) &&
            (PRODUCTS[i].max_allowed === null || get_amount_of_item_orders(PRODUCTS[i].id) < PRODUCTS[i].max_allowed)) {
            let price = create_element('p', ['item-price'], '€' + PRODUCTS[i].price);
            list_item.appendChild(price);
            list_item.setAttribute('onclick', "add_product(" + PRODUCTS[i].id + ")");
            list_item.classList.add('btn-on');
        }
        else {
            let maximum = create_element('p', [], 'Maximum reached');
            list_item.appendChild(maximum);
            list_item.classList.add('btn-off');
        }
        base.appendChild(list_item);
    }

    if (PRODUCTS.length === 0) {
        PRODUCT_CONTAINER.innerHTML = "<p class='alert-warning'>There are no products you can order.</p>";
    }
    else {
        PRODUCT_CONTAINER.innerHTML = "";
        PRODUCT_CONTAINER.append(base);
    }
}

function construct_order_section() {
    let base = document.createElement('div');
    base.classList.add('product-list');
    let cart = get_cart_list();
    for (let i = 0; i < cart.length; i++) {
        let product = find_product_details(cart[i]);
        if (product !== null) {
            let list_item = create_element('div', ['btn-ml', 'btn-on'], '');
            list_item.setAttribute('onclick', "delete_product(" + product.id + ")");
            let icon = create_element('i', ['fas', 'fa-' + product.icon], '');
            let name = create_element('h2', ['item-name'], 'Click to remove ' + product.name);
            let price = create_element('p', ['item-price'], '€' + product.price);

            list_item.appendChild(icon);
            list_item.appendChild(name);
            list_item.appendChild(price);
            base.appendChild(list_item);
        }
    }

    if (cart.length === 0) {
        ORDER_CONTAINER.innerHTML = "<p class='alert-warning'>You have not ordered any items yet.</p>";
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
            console.log(cart);
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
    return cart.length
}

function add_product(product_id) {
    if (get_amount_of_cart_items() < MAX_ORDERS) {
        let cart = get_cart_list();
        let product_details = find_product_details(product_id);
        if (product_details !== null) {
            cart.push(product_id);
            set_cart_list(cart);
            refresh();
            return true;
        }
        else {
            return false;
        }
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

function refresh() {
    construct_products_section();
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