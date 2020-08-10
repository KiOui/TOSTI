var _scannerIsRunning = false;

let scanned_codes = [];

function start_scanner() {
    Quagga.init({
        inputStream: {
            name: "Live",
            type: "LiveStream",
            target: document.querySelector('#scanner'),
            constraints: {
                width: 480,
                height: 320,
                facingMode: "environment"
            },
        },
        decoder: {
            readers: [
                "ean_reader",
                "ean_8_reader"
            ],
            debug: {
                showCanvas: true,
                showPatches: true,
                showFoundPatches: true,
                showSkeleton: true,
                showLabels: true,
                showPatchLabels: true,
                showRemainingPatchLabels: true,
                boxFromPatches: {
                    showTransformed: true,
                    showTransformedBox: true,
                    showBB: true
                }
            },
            multiple: false
        },

    }, function (err) {
        if (err) {
            console.log(err);
            return
        }

        Quagga.start();
    });

    Quagga.onProcessed(function (result) {
        var drawingCtx = Quagga.canvas.ctx.overlay,
            drawingCanvas = Quagga.canvas.dom.overlay;

        if (result) {
            if (result.boxes) {
                drawingCtx.clearRect(0, 0, parseInt(drawingCanvas.getAttribute("width")), parseInt(drawingCanvas.getAttribute("height")));
                result.boxes.filter(function (box) {
                    return box !== result.box;
                }).forEach(function (box) {
                    Quagga.ImageDebug.drawPath(box, {x: 0, y: 1}, drawingCtx, {color: "green", lineWidth: 2});
                });
            }

            if (result.box) {
                Quagga.ImageDebug.drawPath(result.box, {x: 0, y: 1}, drawingCtx, {color: "#00F", lineWidth: 2});
            }

            if (result.codeResult && result.codeResult.code) {
                Quagga.ImageDebug.drawPath(result.line, {x: 'x', y: 'y'}, drawingCtx, {color: 'red', lineWidth: 3});
            }
        }
    });


    Quagga.onDetected(scan_result);

    SCANNER.style.display = "";
    SCANNER_START_BUTTON.style.display = "none";
}

function get_product_details_from_barcode(data_url, csrf_token, callback_ok, callback_error, barcode /*, args */) {
    let args = Array.prototype.slice.call(arguments, 5);
    jQuery(function($) {
        let data = {
            'csrfmiddlewaretoken': csrf_token,
            'barcode': barcode,
            'option': 'barcode'
        };
        $.ajax({type: 'POST', url: data_url, data, dataType:'json', asynch: true, success:
            function(data) {
                if (data.error) {
                    args.unshift(data.error);
                    callback_error.apply(args);
                }
                else {
                    args.unshift(data.products);
                    callback_ok.apply(this, args);
                }
            }}).fail(function() {
                args.unshift("Error while getting product data.");
                callback_error.apply(this, args);
            });
        }
    )
}

function create_popup_button(product) {
    let base = create_element("input", ["popup-button", "btn-ml", "btn-on"], product.name);
    base.type = "button";
    base.value = product.name;
    base.addEventListener("click", add_product.bind(self, DATA_URL, CSRF_TOKEN, product_added_succeeded, product_added_failed, product));
    return base;
}

function stop_scanner() {
    Quagga.stop();
    SCANNER.style.display = "none";
    SCANNER_START_BUTTON.style.display = "";
}

function product_scanned(products) {
    if (products.length > 0) {
        stop_scanner();
        scanned_codes = [];
        POPUP_MODAL_BODY.innerHTML = "";
        for (let i = 0; i < products.length; i++) {
            let button = create_popup_button(products[i]);
            POPUP_MODAL_BODY.append(button);
        }
        $(POPUP_MODAL).modal("show");
    }
}

function product_error() {
    console.log("No product data for this barcode.");
}

function scan_result(result) {
    let code = result.codeResult.code;
    if (!scanned_codes.includes(code)) {
        scanned_codes.push(code);
        get_product_details_from_barcode(DATA_URL, CSRF_TOKEN, product_scanned, product_error, code);
    }
}

function add_product(data_url, csrf_token, callback_ok, callback_error, product /*, args */) {
    $(POPUP_MODAL).modal("hide");
    let args = Array.prototype.slice.call(arguments, 5);
    jQuery(function($) {
        let data = {
            'csrfmiddlewaretoken': csrf_token,
            'option': 'add',
            'product': product.id
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
                args.unshift("Error while adding a product.");
                callback_error.apply(this, args);
            });
        }
    )
}

function product_added_succeeded() {
    MESSAGE_CONTAINER.innerHTML = "";
    MESSAGE_CONTAINER.append(create_element("p", ["alert", "alert-success"], "Product added successfully!"))
}

function product_added_failed(errormsg) {
    MESSAGE_CONTAINER.innerHTML = "";
    MESSAGE_CONTAINER.append(create_element("p", ["alert", "alert-danger"], errormsg))
}

start_scanner();