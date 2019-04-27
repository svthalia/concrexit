$(function () {
    var signatureField = $('#id_signature');
    var signatureCanvas = document.getElementById("id_signature_canvas");
    var signaturePad = new SignaturePad(signatureCanvas);

    function canvasToField() {
        if (signaturePad.toData().length) {
            signatureField.val(signaturePad.toDataURL());
        }
    }

    signaturePad.fromDataURL(signatureField.val());
    signaturePad.onEnd = canvasToField;


    function resizeCanvas() {
        var ratio = Math.max(window.devicePixelRatio || 1, 1);
        signatureCanvas.width = signatureCanvas.offsetWidth * ratio;
        signatureCanvas.height = signatureCanvas.offsetHeight * ratio;
        signatureCanvas.getContext("2d").scale(ratio, ratio);
        signaturePad.clear(); // otherwise isEmpty() might return incorrect value
    }

    window.addEventListener("resize", resizeCanvas);
    resizeCanvas();

    $('#canvas-undo-btn').click(function (e) {
        e.preventDefault();
        var data = signaturePad.toData();
        if (data) {
            data.pop();
            signaturePad.fromData(data);

            if (data.length) {
                canvasToField();
            } else {
                signatureField.val('');
            }
        }
    });

    $('#canvas-clear-btn').click(function (e) {
        e.preventDefault();
        signaturePad.clear();
        signatureField.val('');
    });

    var ddCheckbox = $('#id_direct_debit');

    function showDirectDebitFields() {
        if (ddCheckbox.is(':checked')) {
            $('.direct-debit-fields').removeClass('d-none');
            $('.normal-fields').addClass('col-lg-6');
        } else {
            $('.direct-debit-fields').addClass('d-none');
            $('.normal-fields').removeClass('col-lg-6');
        }
    }

    showDirectDebitFields();
    ddCheckbox.change(showDirectDebitFields);

    // // Returns signature image as data URL (see https://mdn.io/todataurl for the list of possible parameters)
    // signaturePad.toDataURL(); // save image as PNG
    // signaturePad.toDataURL("image/jpeg"); // save image as JPEG
    // signaturePad.toDataURL("image/svg+xml"); // save image as SVG
    //
    // // Draws signature image from data URL.
    // // NOTE: This method does not populate internal data structure that represents drawn signature. Thus, after using #fromDataURL, #toData won't work properly.
    // signaturePad.fromDataURL("data:image/png;base64,iVBORw0K...");
    //
    // // Returns signature image as an array of point groups
    // const data = signaturePad.toData();
    //
    // // Draws signature image from an array of point groups
    // signaturePad.fromData(data);
    //
    // // Clears the canvas
    // signaturePad.clear();
    //
    // // Returns true if canvas is empty, otherwise returns false
    // signaturePad.isEmpty();
    //
    // // Unbinds all event handlers
    // signaturePad.off();
    //
    // // Rebinds all event handlers
    // signaturePad.on();
});



