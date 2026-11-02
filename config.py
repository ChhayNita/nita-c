import os

class Config:
    SECRET_KEY = 'auracart_secret_key_12345'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'uploads')

    # Bakong KHQR Integration Settings
    BAKONG_ID = os.getenv("BAKONG_ID", "chey_kimrith@bkrt")
    BAKONG_MERCHANT_NAME = os.getenv("BAKONG_MERCHANT_NAME", "NitaSV7 Ecommerce")
    BAKONG_MERCHANT_CITY = os.getenv("BAKONG_MERCHANT_CITY", "Phnom Penh")
    BAKONG_ACQUIRING_ID = os.getenv("BAKONG_ACQUIRING_ID", "chey_kimrith@bkrt")
    BAKONG_API_BASE_URL = os.getenv("BAKONG_API_BASE_URL", "https://api-bakong.nbc.gov.kh")
    BAKONG_TOKEN = os.getenv(
        "BAKONG_TOKEN",
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkYXRhIjp7ImlkIjoiZDEyOTZhYzQ2MmFiNGY0OCJ9LCJpYXQiOjE3ODcwNzEyNTcsImV4cCI6MTc5NDg0NzI1N30.qOuwDx-uMqMfcMnyjfOzrx_je8G33ryBP9TUycG4nJU"
    )
