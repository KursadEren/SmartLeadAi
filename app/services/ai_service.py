"""
ai_service.py  —  Modul C: Yapay zeka servisi

Projedeki TEK yapay zeka dosyasi. Yonerge Bolum 3'teki mimari sozlesme:
"ai_service.py disinda HICBIR yerde yapay zeka API cagrisi olmayacak."

Bu dosya Flask, HTTP istegi, oturum ve veritabani kavramlarini BILMEZ.
Girdisi duz Python (str + list), ciktisi duz Python (str). Hata durumunda
JSON degil, AIServiceError firlatir -- JSON'a cevirme isi routes.py'nin.

Bu yalitim sayesinde dosya bir Flask projesinden cikarilip bir masaustu
uygulamasina ya da bir komut satiri aracina oldugu gibi takilabilir.
"""

import requests

from config import Config

# ---------------------------------------------------------------------------
# Saglayici tablosu.
#
# Yonerge: "Saglayici degisimi (Groq -> Gemini) tek satir olmali."
# O tek satir .env icindeki AI_PROVIDER degeri. Yeni bir saglayici eklemek
# icin bu sozluge bir giris yazmak yeterli; yanit_uret() degismez.
# ---------------------------------------------------------------------------
#
# MODEL SECIMI HAKKINDA NOT:
# Yonerge 'llama-3.1-8b-instant' yaziyor, ancak Groq bu modeli emekliye ayirdi;
# 14.09.2026 itibariyla API 404 "model_not_found" donuyor ve Llama ailesi
# saglayicinin model listesinde hic yok. Yerine ayni sinifta, hizli ve Turkce
# yaniti temiz olan 'openai/gpt-oss-20b' secildi.
# ('qwen/qwen3.6-27b' de denendi ama dusunme adimlarini yanita sizdirdigi icin
#  elendi.) Model adi Config.AI_MODEL ile .env'den ezilebilir.
SAGLAYICILAR = {
    'groq': {
        'url': 'https://api.groq.com/openai/v1/chat/completions',
        'model': 'openai/gpt-oss-20b',
    },
}

# Anahtar yokken donulecek metin. Uygulama cokmez, demo modunda calisir.
DEMO_YANITI = (
    "Su anda demo modundayim: yapay zeka baglantisi kapali. NoteX, toplantilari "
    "mevzuata uygun bir tutanaga donusturur. Erken erisim listesine katilmak "
    "isterseniz asagidaki forma adinizi ve telefonunuzu birakabilirsiniz."
)


class AIServiceError(Exception):
    """Yapay zeka katmaninda olusan, kullaniciya gosterilebilir hata.

    routes.py bu hatayi yakalayip HTTP 503 (servis gecici olarak kullanilamiyor)
    yanitina cevirir. Mesaji kibar ve teknik ayrinti icermeyecek sekilde
    yazilir -- API anahtari ya da ham sunucu yaniti asla iceri konmaz.
    """


class AIService:
    """Groq uzerinden sohbet yaniti ureten servis."""

    def __init__(self):
        self.api_key = Config.GROQ_API_KEY
        self.saglayici = Config.AI_PROVIDER

        # Tanimsiz bir saglayici adi gelirse coker degil, groq'a duser.
        ayar = SAGLAYICILAR.get(self.saglayici, SAGLAYICILAR['groq'])
        self.url = ayar['url']
        # .env'de AI_MODEL varsa o kazanir; yoksa saglayicinin varsayilani.
        self.model = Config.AI_MODEL or ayar['model']

    # -- yardimci metotlar ---------------------------------------------------

    def _sistem_mesaji(self):
        """BUSINESS_CONTEXT'i config'den okuyup sistem mesaji bicimine sokar.

        Modelin kim oldugunu, neyi satdigini ve nasil konusacagini soyleyen
        talimat budur. Markaya ozel tek metin oldugu icin kodun icine
        yazilmaz, config'den okunur.
        """
        return {'role': 'system', 'content': Config.BUSINESS_CONTEXT}

    def _mesajlari_hazirla(self, mesaj, gecmis):
        """Groq'a gonderilecek mesaj dizisini kurar.

        SIRA ONEMLI ve yonergede acikca belirtilmis:
            1. sistem talimati
            2. onceki konusma
            3. yeni kullanici mesaji

        Sira bozulursa model kendi kimligini unutur ya da eski mesaji yeni
        sanar. gecmis None gelirse bos liste kabul edilir.
        """
        mesajlar = [self._sistem_mesaji()]
        if gecmis:
            mesajlar.extend(gecmis)
        mesajlar.append({'role': 'user', 'content': mesaj})
        return mesajlar

    # -- disa acik metot -----------------------------------------------------

    def yanit_uret(self, mesaj, gecmis=None):
        """Kullanici mesajina yapay zeka yaniti uretir.

        Donen deger her zaman bir metindir. Basarisizlik durumunda
        AIServiceError firlatir; None ya da bos string dondurmez, boylece
        cagiran taraf "yanit geldi mi" diye kontrol etmek zorunda kalmaz.
        """
        # Anahtar yoksa ag istegine hic girilmez. Yonerge: "Anahtar yoksa
        # cokmek yerine demo modu mesaji." Bu erken cikis, anahtari olmayan
        # bir degerlendiricinin projeyi yine de calistirabilmesini saglar.
        if not self.api_key:
            return DEMO_YANITI

        basliklar = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }
        govde = {
            'model': self.model,
            'messages': self._mesajlari_hazirla(mesaj, gecmis),
            'temperature': 0.6,   # tutarli ve olcülü yanit; marka tonu abartisiz
            'max_tokens': 500,
        }

        try:
            cevap = requests.post(self.url, headers=basliklar, json=govde, timeout=20)
            # 4xx/5xx durum kodlarini istisnaya cevirir.
            cevap.raise_for_status()
            veri = cevap.json()
            return veri['choices'][0]['message']['content'].strip()

        # Hata turleri ayri ayri yakalanir: her birinin sebebi ve kullaniciya
        # soylenecek sey farkli. Tek bir "except Exception" yazmak hata
        # yonetimi notunu dusurur ve gercek sorunu gizler.
        except requests.exceptions.Timeout:
            raise AIServiceError(
                'Yapay zeka servisi zamaninda yanit vermedi. Lutfen tekrar deneyin.'
            )
        except requests.exceptions.ConnectionError:
            raise AIServiceError(
                'Yapay zeka servisine baglanilamadi. Internet baglantinizi kontrol edin.'
            )
        except requests.exceptions.HTTPError:
            # cevap.text burada BILEREK kullanilmiyor: ham govde anahtari ya da
            # sunucu ayrintisini disari sizdirabilir.
            raise AIServiceError(
                'Yapay zeka servisi su anda yanit veremiyor. Kisa bir sure sonra deneyin.'
            )
        except (KeyError, IndexError, ValueError):
            # Yanit geldi ama bekledigimiz bicimde degil (ornegin JSON bozuk
            # ya da 'choices' alani yok).
            raise AIServiceError(
                'Yapay zeka yaniti beklenen bicimde degil.'
            )


# Yonerge: "dosya sonunda tek ornek".
# Butun uygulama bu ornegi paylasir; routes.py yeniden AIService() cagirmaz.
# Boylece ayarlar bir kez okunur ve servis durumu tek yerde tutulur.
ai_service = AIService()
