function update_order(checkbox, order_id, property, callback) {
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
                    console.warning("Updating order failed");
                }
                else {
                    args.unshift(checkbox);
                    args.unshift(data.value);
                    callback.apply(this, args);
                }
            }}).fail(function() {
                console.error("Error while getting order data");
            });
        }
    )
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