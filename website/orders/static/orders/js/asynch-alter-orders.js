function update_order(data_url, checkbox, property, callback) {
    update_and_callback(
        data_url,
        {'value': checkbox.classList.contains('btn-danger'), 'property': property},
        callback,
        checkbox
    );
}

function update_checkbox(data, checkbox) {
    let value = data.value;
    checkbox.classList.remove('btn-success');
    checkbox.classList.remove('btn-danger');
    if (value) {
        checkbox.classList.add('btn-success');
    }
    else {
        checkbox.classList.add('btn-danger');
    }
}

function remove_order(data_url) {
    if (window.confirm("Do you want to delete this order?")) {
        update_and_callback(
            data_url,
            {},
            update_update_list
        );
    }
}