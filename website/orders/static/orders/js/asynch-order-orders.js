
let MAX_ORDERS = 5;
let PRODUCTS = [];


function get_amount_of_item_orders(product_id) {
    let amount_of_items = 0;
    for (let i = 0; i < vue.cart.length; i++) {
        if (vue.cart[i].id === product_id) {
            amount_of_items += 1;
        }
    }
    return amount_of_items;
}

function delete_product(product_id) {
    for (let i = 0; i < vue.cart.length; i++) {
        if (vue.cart[i].id === product_id) {
            vue.cart.splice(i, 1);
            set_cart_list(vue.cart);
            return;
        }
    }
}

function find_product_details(product_id) {
    for (let i = 0; i < vue.products.length; i++) {
        if (vue.products[i].id === product_id) {
            return vue.products[i];
        }
    }
    return null;
}

function get_amount_of_cart_items() {
    return vue.cart.length;
}

function get_amount_of_restricted_cart_items() {
    return vue.cart.filter(
        function(value, index, arr)
        {
            return !value.ignore_shift_restrictions;
    }).length;
}

function add_product(product_id) {
    let product_details = find_product_details(product_id);
    if (product_details !== null && (get_amount_of_restricted_cart_items() < vue.shift.max_user_orders || product_details.ignore_shift_restrictions)) {
        vue.cart.push(product_details);
        set_cart_list(vue.cart);
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
        if (!products[i].ignore_shift_restrictions) {
            ret.push(products[i]);
        }
    }
    return ret;
}

function get_unrestricted_products(products) {
    let ret = [];
    for (let i = 0; i < products.length; i++) {
        if (products[i].ignore_shift_restrictions) {
            ret.push(products[i]);
        }
    }
    return ret;
}

function order_callback(data) {
    vue.loading = false;
    vue.cart = [];
    set_cart_list([]);
    update_update_list();
    alert("Your order has been placed!");
}

function order_error_callback(data) {
    vue.loading = false;
    let error_msg = "The following errors occurred: ";
    data.responseJSON.forEach(error => error_msg = error_msg.concat(`${error}; `));
    alert(error_msg);
}