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