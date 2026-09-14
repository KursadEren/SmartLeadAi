"""
config.py  —  Modul A: Yapilandirma katmani

Bu dosya projedeki TEK ayar kaynagidir. Gorevi, gizli anahtarlari ve ortama
gore degisen degerleri .env dosyasindan okuyup uygulamanin geri kalanina
sinif oznitelikleri olarak sunmaktir.

Mimari sozlesme: Bu dosya proje icinden HICBIR modulu import etmez; yalnizca
os ve dotenv kullanir. Aksi halde dairesel import dogar (config -> database
-> config) ve uygulama hic baslamaz.
"""

import os

from dotenv import load_dotenv

# .env dosyasindaki degerleri ortam degiskenlerine yukler.
# Bu cagri sinif tanimlarindan ONCE yapilmak zorunda: sinif govdeleri import
# aninda calisir, yani asagidaki os.environ.get(...) satirlari dosya import
# edilir edilmez degerlendirilir. load_dotenv() sonra cagrilirsa hepsi bos kalir.
#
# Not: load_dotenv varsayilan olarak MEVCUT ortam degiskenlerini EZMEZ.
# Bu davranis bilincli olarak korunuyor; sayesinde
#   GROQ_API_KEY= python run.py
# komutuyla demo modu test edilebiliyor ve Render'da panelden girilen
# degiskenler .env'e gore oncelikli oluyor.
load_dotenv()


# ---------------------------------------------------------------------------
# Markaya ozel TEK metin.
#
# Yonerge Bolum 1.2: "BUSINESS_CONTEXT disinda hicbir kodu konuya ozel
# yazmayin." Mimari herkes icin ayni; konu degisirse yalnizca bu metin degisir.
# Sablonu bir kafeye, hukuk burosuna ya da spor salonuna uyarlamak icin
# asagidaki uc tirnakli metni degistirmek yeterlidir.
#
# Turkce karakter kullanilmadi: metin HTTP govdesiyle Groq'a gidiyor ve
# kodlama farkliliklarindan kaynaklanan sorunlari bastan elemek icin.
# ---------------------------------------------------------------------------
VARSAYILAN_ISLETME_BAGLAMI = """Sen NoteX'in asistanisin. NoteX, toplantilari
kaydedip mevzuata uygun bir tutanaga donusturen bir mobil uygulamadir; ses
telefonun icinde metne cevrilir, disari cikmaz. Apartman ve site genel
kurullari, dernek yonetim kurullari ve okul kurullari gibi tutanak tutmanin
zorunlu oldugu toplantilara odaklanir.

Ziyaretcinin hangi tur toplanti yaptigini ogren, tutanak surecinde yasadigi
zorlugu sor ve erken erisim listesine katilmasi icin iletisim bilgisi birakmaya
yonlendir.

Sakin, net ve abartisiz konus. Vaatleri somut tut: "yapay zeka destekli devrim"
degil, "tutanak toplanti biterken hazir". Kullaniciya siz diye hitap et. Emoji
kullanma. Yanitlarini kisa tut, en fazla dort cumle."""


class Config:
    """Butun ortamlarin paylastigi temel ayarlar.

    Her ayar os.environ.get('ANAHTAR', 'varsayilan') deseniyle okunur.
    Ikinci parametre sayesinde .env eksik olsa bile uygulama coker degil,
    makul bir varsayilanla calisir.
    """

    # Flask oturum cerezlerini imzalar. Uretimde mutlaka .env'den gelmeli.
    SECRET_KEY = os.environ.get('SECRET_KEY', 'gelistirme-icin-gecici-anahtar')

    # SQLite dosyasinin yolu. database.py disinda kimse kullanmaz.
    DATABASE_URL = os.environ.get('DATABASE_URL', 'smartlead.db')

    # Groq API anahtari. Varsayilan bos string -- None degil.
    # Boylece ai_service icinde tek bicimli bir "if not self.api_key" kontrolu
    # yeterli oluyor, ayrica None kontrolu gerekmiyor.
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')

    # Hangi yapay zeka saglayicisi kullanilacak. ai_service.py bu degere
    # bakarak url ve model secer; saglayici degisimi tek satirlik is olur.
    AI_PROVIDER = os.environ.get('AI_PROVIDER', 'groq')

    # Model adi. Bos birakilirsa ai_service kendi saglayici tablosundaki
    # varsayilani kullanir. Ortamdan ezilebilir olmasi bilincli: saglayicilar
    # modelleri emekliye ayirdiginda kod degistirmeden .env'den gecis yapilir.
    AI_MODEL = os.environ.get('AI_MODEL', '')

    # Tarayiciya hangi kaynaklardan istek kabul edilecegini soyler.
    # Gelistirmede '*', uretimde yalnizca Wix adresi olmali.
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*')

    # Yapay zekaya verilen sistem talimati (yukaridaki metin).
    # Ortamdan da ezilebilir; boylece Render panelinden metni degistirmek
    # icin yeniden dagitim gerekmez.
    BUSINESS_CONTEXT = os.environ.get('BUSINESS_CONTEXT', VARSAYILAN_ISLETME_BAGLAMI)


class DevelopmentConfig(Config):
    """Yerel gelistirme: hata sayfalari ayrintili, otomatik yeniden yukleme acik."""

    DEBUG = True


class ProductionConfig(Config):
    """Render uzerinde calisan surum: hata ayrintilari ziyaretciye gosterilmez."""

    DEBUG = False


# create_app() bu sozlukten ortam adina gore dogru sinifi secer.
# 'default' anahtari, tanimsiz bir ortam adi gelirse cokmeyi onler.
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}
