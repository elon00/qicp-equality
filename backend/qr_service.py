"""Dynamic Multi-Cryptocurrency QR Code Generator for QICP Equality.

Generates scan-ready QR codes for field workers, grassroots micro-merchants,
and community donors across:
- Native ICP & QICP (ICRC-1)
- Bitcoin & ckBTC
- Ethereum & ckETH
- Universal Decentralized Intent Link
"""
import base64
import io
import qrcode
from typing import Dict, Optional


class MultiCryptoQRService:
    """Service generating standards-compliant multi-chain payment QR codes."""

    @staticmethod
    def generate_payment_uri(
        currency: str,
        recipient_address: str,
        amount: Optional[float] = None,
        memo: Optional[str] = None,
    ) -> str:
        """Format standard URI schema based on currency."""
        curr = currency.upper().strip()
        if curr in ("QICP", "ICP"):
            uri = f"icp:{recipient_address}"
            params = []
            if amount is not None:
                params.append(f"amount={amount}")
            if curr == "QICP":
                params.append("token=QICP")
            if memo:
                params.append(f"memo={memo}")
            if params:
                uri += "?" + "&".join(params)
            return uri

        elif curr in ("BTC", "CKBTC"):
            uri = f"bitcoin:{recipient_address}"
            if amount is not None:
                uri += f"?amount={amount}"
            return uri

        elif curr in ("ETH", "CKETH"):
            uri = f"ethereum:{recipient_address}"
            if amount is not None:
                uri += f"?value={int(amount * 1e18)}"
            return uri

        else:
            # Universal QICP Intent URI
            uri = f"qicp://pay?to={recipient_address}&asset={curr}"
            if amount is not None:
                uri += f"&amount={amount}"
            if memo:
                uri += f"&memo={memo}"
            return uri

    @classmethod
    def generate_qr_data_uri(
        cls,
        currency: str,
        recipient_address: str,
        amount: Optional[float] = None,
        memo: Optional[str] = None,
    ) -> Dict[str, str]:
        """Generate QR image and encode as base64 data URI."""
        uri = cls.generate_payment_uri(currency, recipient_address, amount, memo)

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="#001830", back_color="#ffffff")
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_bytes = buffered.getvalue()

        b64_str = base64.b64encode(img_bytes).decode("utf-8")
        data_uri = f"data:image/png;base64,{b64_str}"

        return {
            "currency": currency.upper(),
            "recipient": recipient_address,
            "amount": amount,
            "payment_uri": uri,
            "qr_data_uri": data_uri,
        }


if __name__ == "__main__":
    print("Testing MultiCryptoQRService...")
    res = MultiCryptoQRService.generate_qr_data_uri(
        currency="QICP",
        recipient_address="rdmx6-jaaaa-aaaaa-aaadq-cai",
        amount=500.0,
        memo="grant-community-001",
    )
    print(f"Generated URI: {res['payment_uri']}")
    print(f"QR Data URI Length: {len(res['qr_data_uri'])} chars")
