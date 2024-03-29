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


    Quagga.onDetected(detected_qr_code_or_barcode);
}

function stop_scanner() {
    scanned_codes = [];
    Quagga.stop();
}

function detected_qr_code_or_barcode(result) {
    if (!result.codeResult) {
        return;
    }

    if (result.codeResult.format === "qr_code") {
        return scan_qr_code(result);
    } else {
        return add_product_from_barcode(result);
    }
}

function scan_qr_code(result) {
    let qrcode = result.codeResult.code;
    if (!scanned_codes.includes(qrcode)) {
        scanned_codes.push(qrcode);
        fetch(
            TRANSACTION_USER_DATA_URL,
            {
                method: 'POST',
                body: JSON.stringify({
                    'csrfmiddlewaretoken': get_csrf_token(),
                    'token': qrcode,
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
            tata.success('', `Scanned user ${data.user.display_name}`);
            transaction_vue.account = data;
            const modal = new bootstrap.Modal(document.getElementById(TRANSACTION_POPUP_MODAL_ID));
            modal.show();
        }).catch(error => {
            console.log(error);
            if (error.status === 404) {
                tata.error("", "The user was identified but does not have an open account yet. Please first open an account and then scan the QR code again.")
            } else {
                tata.error("", "The QR code is not valid (anymore), please scan a new QR code.")
            }
        }).finally(() => {
            Quagga.stop();
            scanned_codes = [];
            let modal = bootstrap.Modal.getInstance(document.getElementById(POPUP_MODAL_ID));
            modal.hide();
        });
    }
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
            console.log("No product data for barcode " + barcode + " .");
        });
    }
}