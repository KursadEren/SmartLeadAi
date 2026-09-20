# SmartLead AI — NoteX

Ziyaretçilerle yapay zekâ üzerinden sohbet eden ve iletişim bilgilerini (lead) toplayan
bir sistem. HumanPorts 51. Dönem bitirme projesi.

**Konu:** NoteX — toplantıları kaydedip mevzuata uygun bir tutanağa dönüştüren mobil
uygulama. Asistan, ziyaretçinin hangi tür toplantı yaptığını öğrenir, tutanak sürecindeki
zorluğunu sorar ve erken erişim listesine yönlendirir.

## Ne yapıyor

- **Karşılama sayfası** (`/`) — ziyaretçi asistanla sohbet eder, isim ve telefon bırakır
- **Yönetim paneli** (`/dashboard`) — toplanan kayıtlar en yeniden eskiye listelenir

## Mimari

Her dosyanın tek bir sorumluluğu var:

```
smartlead_ai/
├── run.py              Giriş noktası
├── config.py           Ayarlar (.env okur)
├── requirements.txt
├── .env                Gizli anahtarlar — Git'e gitmez
├── .gitignore
└── app/
    ├── __init__.py     create_app() fabrikası, CORS, /health
    ├── database.py     SQLite işlemleri — projedeki TEK SQL
    ├── routes.py       HTTP rotaları — sadece yönlendirir
    ├── templates/
    │   ├── index.html
    │   └── dashboard.html
    └── services/
        ├── __init__.py
        └── ai_service.py   Groq çağrıları — projedeki TEK AI
```

`database.py` dışında hiçbir yerde SQL, `ai_service.py` dışında hiçbir yerde yapay zekâ
çağrısı yok. `routes.py` yalnızca bu iki katmanın fonksiyonlarını çağırır.

## API

| Metot | Yol | Görevi |
|---|---|---|
| GET | `/` | Karşılama sayfası |
| GET | `/dashboard` | Yönetim paneli |
| GET | `/health` | Sunucu ayakta mı |
| POST | `/api/sohbet` | `{mesaj, gecmis}` → `{basari, cevap}`; soru-cevap kaydedilir |
| POST | `/api/leads` | `{isim, telefon, mesaj}` → 201 |
| GET | `/api/leads` | `{basari, adet, leads}` |
| GET | `/api/sohbetler` | `{basari, adet, sohbetler}` |

Her yanıt `basari` alanı içerir. Eksik veri **400**, yapay zekâ hatası **503**,
veritabanı hatası **500**, yeni kayıt **201**.

## Kurulum

```bash
git clone https://github.com/KursadEren/SmartLeadAi.git
cd SmartLeadAi
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

`.env` dosyası oluştur:

```
GROQ_API_KEY=gsk_...
SECRET_KEY=rastgele-uzun-bir-metin
AI_PROVIDER=groq
AI_MODEL=openai/gpt-oss-20b
DATABASE_URL=smartlead.db
CORS_ORIGINS=*
FLASK_ENV=development
```

Çalıştır:

```bash
python run.py
```

`http://127.0.0.1:5000` adresini aç.

> macOS'ta 5000 portunu AirPlay Receiver kullanıyor olabilir.
> O durumda: `PORT=5001 python run.py`

## Ortam değişkenleri

| Değişken | Ne işe yarar |
|---|---|
| `GROQ_API_KEY` | Groq API anahtarı. Boşsa uygulama çökmez, demo modunda çalışır |
| `SECRET_KEY` | Flask oturum imzası |
| `AI_PROVIDER` | Yapay zekâ sağlayıcısı (`groq`) |
| `AI_MODEL` | Model adı. Boşsa varsayılan kullanılır |
| `DATABASE_URL` | SQLite dosyasının yolu |
| `CORS_ORIGINS` | İzin verilen kaynaklar. Üretimde `*` yerine site adresi |
| `FLASK_ENV` | `development` veya `production` |

## Test

```bash
curl http://127.0.0.1:5000/health

curl -X POST http://127.0.0.1:5000/api/sohbet \
  -H 'Content-Type: application/json' \
  -d '{"mesaj":"Apartman genel kurulu tutanagi nasil hazirlanir?","gecmis":[]}'

curl -X POST http://127.0.0.1:5000/api/leads \
  -H 'Content-Type: application/json' \
  -d '{"isim":"Ornek Kisi","telefon":"05551112233","mesaj":"Erken erisim"}'

curl http://127.0.0.1:5000/api/leads
```

## Yayın

Render'da Web Service olarak çalışır:

- Build: `pip install -r requirements.txt`
- Start: `gunicorn run:app`
- Ortam değişkenleri Render panelinden girilir (`.env` depoya yüklenmez)

## Not

Yönergede model olarak `llama-3.1-8b-instant` belirtilmiş, ancak Groq bu modeli emekliye
ayırdı ve API `404 model_not_found` dönüyor. Yerine `openai/gpt-oss-20b` kullanıldı.
Model adı `.env` içindeki `AI_MODEL` ile değiştirilebilir.

## Teknolojiler

Python · Flask · SQLite · Groq API · Gunicorn · Wix Velo
