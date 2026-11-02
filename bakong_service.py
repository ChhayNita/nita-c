import io
import base64
import os
import qrcode
from flask import current_app
from bakong_khqr import KHQR


def get_bakong_client():
    token = current_app.config.get("BAKONG_TOKEN") or os.getenv("BAKONG_TOKEN")
    return KHQR(bakong_token=token)


def generate_bakong_khqr(amount: float, bill_number: str, currency: str = "USD", store_label: str = "SV7 Store"):
    """
    Generate Bakong KHQR string, MD5 hash, and Base64 QR Image.
    """
    client = get_bakong_client()
    account_id = current_app.config.get("BAKONG_ID", "chey_kimrith@bkrt")
    merchant_name = current_app.config.get("BAKONG_MERCHANT_NAME", "Ecommerce")
    merchant_city = current_app.config.get("BAKONG_MERCHANT_CITY", "Phnom Penh")

    # Generate KHQR using bakong-khqr library
    response = client.create_qr(
        amount=round(float(amount), 2),
        account_id=account_id,
        merchant_name=merchant_name,
        merchant_city=merchant_city,
        currency=currency,
        bill_number=bill_number,
        store_label=store_label
    )

    qr_string = getattr(response, "qr", str(response))
    md5_hash = getattr(response, "md5", None)
    if not md5_hash:
        md5_hash = client.generate_md5(qr_string)

    # Generate Base64 QR code image
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2,
    )
    qr.add_data(qr_string)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0f172a", back_color="#ffffff")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    qr_image_base64 = f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode('utf-8')}"

    # Generate mobile app deep link if supported
    deeplink = None
    try:
        deeplink = client.generate_deeplink(qr_string)
    except Exception:
        deeplink = f"https://bakong.nbc.gov.kh/deeplink?qr={qr_string}"

    return {
        "qr": qr_string,
        "md5": md5_hash,
        "qr_image": qr_image_base64,
        "deeplink": deeplink,
        "amount": round(float(amount), 2),
        "currency": currency,
        "merchant_name": merchant_name,
        "bill_number": bill_number
    }


def check_bakong_payment_status(md5: str):
    """
    Check transaction status with Bakong open API.
    Returns: 'PAID', 'UNPAID', 'EXPIRED', or 'SCANNED'
    """
    client = get_bakong_client()
    try:
        status = client.check_payment(md5)
        if isinstance(status, tuple):
            status = status[0]
        return str(status).upper()
    except Exception as e:
        if current_app:
            current_app.logger.warning("Error checking Bakong payment for %s: %s", md5, e)
        return "UNPAID"
