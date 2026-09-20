# config.py - Uygulama ayarlari
# Butun ayarlar .env dosyasindan okunur.

import os
from dotenv import load_dotenv

# .env dosyasini yukler. Sinif tanimlarindan once olmali,
# yoksa asagidaki degerler bos gelir.
load_dotenv()


# Yapay zekaya verilen talimat. Marka degisirse sadece burasi degisir.
ISLETME_BAGLAMI = """Sen NoteX'in asistanisin. NoteX, toplantilari kaydedip
mevzuata uygun bir tutanaga donusturen bir mobil uygulamadir; ses telefonun
icinde metne cevrilir, disari cikmaz. Apartman ve site genel kurullari, dernek
yonetim kurullari ve okul kurullari gibi tutanak tutmanin zorunlu oldugu
toplantilara odaklanir.

Ziyaretcinin hangi tur toplanti yaptigini ogren, tutanak surecinde yasadigi
zorlugu sor ve erken erisim listesine katilmasi icin iletisim bilgisi birakmaya
yonlendir.

Sakin ve abartisiz konus. Kullaniciya siz diye hitap et. Emoji kullanma.
Yanitlarini kisa tut, en fazla dort cumle."""


class Config:
    # os.environ.get(anahtar, varsayilan) -> .env eksikse uygulama yine calisir
    SECRET_KEY = os.environ.get('SECRET_KEY', 'gecici-anahtar')
    DATABASE_URL = os.environ.get('DATABASE_URL', 'smartlead.db')
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
    AI_PROVIDER = os.environ.get('AI_PROVIDER', 'groq')
    AI_MODEL = os.environ.get('AI_MODEL', '')
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*')
    BUSINESS_CONTEXT = os.environ.get('BUSINESS_CONTEXT', ISLETME_BAGLAMI)


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


# create_app bu sozlukten dogru sinifi secer
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}
