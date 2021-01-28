let scanned_codes = [];

function start_scanner() {
    Quagga.init({
        numOfWorkers: 4,
        frequency: 5,
        inputStream: {
            name: "Live",
            type: "LiveStream",
            target: document.querySelector('#scanner'),
            constraints: {
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
        let drawingCtx = Quagga.canvas.ctx.overlay,
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
}

function add_product_from_barcode(data_url, callback_ok, callback_error, barcode /*, args */) {
    let args = Array.prototype.slice.call(arguments, 4);
    jQuery(function($) {
        let data = {
            'csrfmiddlewaretoken': get_csrf_token(),
            'barcode': barcode,
        };
        $.ajax({type: 'POST', url: data_url, data, dataType:'json', asynch: true, success:
            function(data) {
                args.unshift(data);
                callback_ok.apply(this, args);
            }}).fail(function() {
                args.unshift("Error while getting product data.");
                callback_error.apply(this, args);
            });
        }
    )
}

function stop_scanner() {
    scanned_codes = [];
    Quagga.stop();
}

function product_scanned(order) {
    stop_scanner();
    scanned_codes = [];
    $(POPUP_MODAL).modal('hide');
    toastr.success("Added " + order.product.name + " (€" + order.order_price + ") to the queue.");
    if (typeof(update_update_list) !== 'undefined') {
        update_update_list();
    }
}

function product_error(errormsg, barcode) {
    console.log(errormsg);
    console.log("No product data for barcode " + barcode + " .");
}

function scan_result(result) {
    let code = result.codeResult.code;
    if (!scanned_codes.includes(code)) {
        scanned_codes.push(code);
        add_product_from_barcode(SCANNER_DATA_URL, product_scanned, product_error, code, code);
    }
}