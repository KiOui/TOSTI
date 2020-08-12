from django.core.exceptions import ValidationError


def validate_barcode(value):
    """
    Validate a barcode.

    Checks if the barcode is all digits, of the required length and if the checksum is correct
    :param value: the value to validate
    :return: None, raises ValidationError if a check fails
    """
    if value is None:
        return

    if not value.isdigit():
        raise ValidationError("A barcode must consist of only digits")

    if len(value) == 8:
        value = "000000" + value
    elif len(value) == 13:
        value = "0" + value
    else:
        raise ValidationError("A barcode must be either 8 or 13 integers long")

    counter = 0
    for index, digit in enumerate(value[: len(value) - 1]):
        if index % 2 == 0:
            counter += int(digit) * 3
        else:
            counter += int(digit)

    if (10 - (counter % 10)) % 10 != int(value[len(value) - 1]):
        raise ValidationError("The checksum of the barcode is not correct")
