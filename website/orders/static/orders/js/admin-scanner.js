let scanned_codes = [];
class QrCodeReader {
    constructor(config, supplements) {
        // Quagga may have a dependency on the name of the property _row
        this._row = [];
        this.config = config || {};
        this.supplements = supplements;
        this.FORMAT = {
            value: 'qr_code',
            writeable: false,
        };
        return this;
    }

    decodeImage(inputImageWrapper) {
        const data = inputImageWrapper.getAsRGBA();
        const result = jsQR(data, inputImageWrapper.size.x, inputImageWrapper.size.y);

        if (result === null) {
            return null;
        } else {
            return Object.assign({
                codeResult: {
                    code: result.data,
                    format: this.FORMAT.value,
                },
                box: [
                    [result.location.bottomLeftCorner.x, result.location.bottomLeftCorner.y],
                    [result.location.topLeftCorner.x, result.location.topLeftCorner.y],
                    [result.location.topRightCorner.x, result.location.topRightCorner.y],
                    [result.location.bottomRightCorner.x, result.location.bottomRightCorner.y],
                ],
            }, result);
        }
    }
    decodePattern(pattern) {
        // STUB, this is probably meaningless to QR, but needs to be implemented for Quagga, in case
        // it thinks there's a potential barcode in the image
        return null;
    }
}

Quagga.registerReader('qrcode', QrCodeReader);

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
                "ean_8_reader",
                "qrcode"
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
            let color;
            if (result.codeResult && result.codeResult.format === "qr_code") {
                color = 'green';
            } else {
                color = '#00F';
            }

            if (result.box) {
                drawingCtx.clearRect(0, 0, parseInt(drawingCanvas.getAttribute("width")), parseInt(drawingCanvas.getAttribute("height")));
                Quagga.ImageDebug.drawPath(result.box, {x: 0, y: 1}, drawingCtx, {color: color, lineWidth: 2});
            }

            if (result.codeResult && result.codeResult.code && result.line) {
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
            tata.success("", "Added " + data.product.name + " (€" + data.order_price + ") to the queue.");
            if (typeof (update_refresh_list) !== 'undefined') {
                update_refresh_list();
            }
            let tablist = document.querySelector('#nav-orders-scanned-tab');
            let tab = bootstrap.Tab.getOrCreateInstance(tablist);
            tab.show();
            let modal = bootstrap.Modal.getInstance(document.getElementById(POPUP_MODAL_ID));
            modal.hide();
        }).catch(error => {
            console.log(error);
            console.log("No product data for barcode " + barcode + " .");
        });
    }
}