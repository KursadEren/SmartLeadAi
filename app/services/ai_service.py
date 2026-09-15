# ai_service.py - Yapay zeka servisi
# Groq'a yapilan butun istekler burada. Baska dosyada AI cagrisi yok.
# Bu dosya Flask'i ve veritabanini bilmez.

import requests
from config import Config

GROQ_URL = 'https://api.groq.com/openai/v1/chat/completions'

# Yonergede llama-3.1-8b-instant yaziyor ama Groq bu modeli kaldirmis,
# API 404 donuyor. Onun yerine calisan bir model sectim.
VARSAYILAN_MODEL = 'openai/gpt-oss-20b'

DEMO_YANITI = (
    "Su anda demo modundayim, yapay zeka baglantisi kapali. NoteX toplantilari "
    "mevzuata uygun bir tutanaga donusturur. Erken erisim listesine katilmak "
    "isterseniz asagidaki forma adinizi ve telefonunuzu birakabilirsiniz."
)


class AIServiceError(Exception):
    # routes.py bu hatayi yakalayip kullaniciya 503 donuyor
    pass


class AIService:

    def __init__(self):
        self.api_key = Config.GROQ_API_KEY
        self.saglayici = Config.AI_PROVIDER
        self.url = GROQ_URL
        # .env'de AI_MODEL varsa onu kullan, yoksa varsayilani
        self.model = Config.AI_MODEL or VARSAYILAN_MODEL

    def sistem_mesaji(self):
        # Modele kim oldugunu ve nasil konusacagini soyleyen talimat
        return {'role': 'system', 'content': Config.BUSINESS_CONTEXT}

    def mesajlari_hazirla(self, mesaj, gecmis):
        # Sira onemli: once talimat, sonra eski konusma, en son yeni mesaj
        mesajlar = [self.sistem_mesaji()]
        if gecmis:
            mesajlar.extend(gecmis)
        mesajlar.append({'role': 'user', 'content': mesaj})
        return mesajlar

    def yanit_uret(self, mesaj, gecmis=None):
        # Anahtar yoksa istek atmadan demo cevabi don, uygulama cokmesin
        if not self.api_key:
            return DEMO_YANITI

        basliklar = {
            'Authorization': 'Bearer ' + self.api_key,
            'Content-Type': 'application/json'
        }
        govde = {
            'model': self.model,
            'messages': self.mesajlari_hazirla(mesaj, gecmis),
            'temperature': 0.6,
            'max_tokens': 500
        }

        try:
            cevap = requests.post(self.url, headers=basliklar, json=govde, timeout=20)
            cevap.raise_for_status()
            veri = cevap.json()
            return veri['choices'][0]['message']['content'].strip()

        except requests.exceptions.Timeout:
            raise AIServiceError('Yapay zeka servisi zamaninda yanit vermedi.')
        except requests.exceptions.ConnectionError:
            raise AIServiceError('Yapay zeka servisine baglanilamadi.')
        except requests.exceptions.HTTPError:
            # cevap.text yazmiyoruz, icinde anahtar gibi bilgiler olabilir
            raise AIServiceError('Yapay zeka servisi su anda yanit veremiyor.')
        except (KeyError, IndexError, ValueError):
            raise AIServiceError('Yapay zeka yaniti beklenen bicimde degil.')


# Tek ornek olusturuluyor, butun uygulama bunu kullaniyor
ai_service = AIService()
