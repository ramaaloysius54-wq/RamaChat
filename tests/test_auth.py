from utils.validators import normalize_whatsapp_number, validate_otp_code, validate_whatsapp_number

def test_validators():
    assert normalize_whatsapp_number("081234567890") == "+6281234567890"
    assert validate_whatsapp_number("+6281234567890") is True
    assert validate_otp_code("123456") is True
