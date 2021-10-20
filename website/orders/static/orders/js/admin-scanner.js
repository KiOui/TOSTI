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
            return;
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


    Quagga.onDetected(add_product_from_barcode);
}

function stop_scanner() {
    scanned_codes = [];
    Quagga.stop();
}

function add_product_from_barcode(result) {
    let barcode = result.codeResult.code;
    if (!scanned_codes.includes(barcode)) {
        scanned_codes.push(barcode);
        fetch(
            SCANNER_DATA_URL,
            {
                method: 'POST',
                body: JSON.stringify({
                    'csrfmiddlewaretoken': get_csrf_token(),
                    'barcode': barcode,
                }),
                headers: {
                    "X-CSRFToken": get_csrf_token(),
                    "Accept": 'application/json',
                    "Content-Type": 'application/json',
                }
            }
        ).then(response => {
            if (response.status === 200) {
                return response.json();
            } else {
                throw response;
            }
        }).then(data => {
            Quagga.stop();
            scanned_codes = [];
            toastr.success("Added " + data.product.name + " (€" + data.order_price + ") to the queue.");
            if (typeof (update_refresh_list) !== 'undefined') {
                update_refresh_list();
            }
            document.getElementById(POPUP_MODAL).modal('hide');
        }).catch(error => {
            console.log("No product data for barcode " + barcode + " .");
        });
    }
}