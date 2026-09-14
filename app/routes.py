"""
routes.py  —  Modul D: Yonlendirme katmani

Yonerge Bolum 3: "routes.py yalnizca bu iki katmanin fonksiyonlarini cagiracak."

Bu dosyada SQL YOK ve yapay zeka API cagrisi YOK. Yaptigi uc sey var:
  1. Gelen istegin govdesini dogrulamak (eksik/bozuk veri -> 400)
  2. Dogru katmana yonlendirmek (database.* veya ai_service.*)
  3. Sonucu JSON'a ve dogru HTTP durum koduna cevirmek

Iki Blueprint kullanilir:
  sayfa_bp : HTML sayfalari (onek yok)
  api_bp   : JSON uc noktalari ('/api' oneki create_app icinde verilir)
"""

from flask import Blueprint, jsonify, render_template, request

from app import database
from app.services.ai_service import AIServiceError, ai_service

# Girdi uzunluk sinirlari. Sinirsiz metin hem Groq maliyetini hem de
# veritabanini sismeye acik birakir; ucuz ve etkili bir koruma.
MESAJ_SINIRI = 2000
ALAN_SINIRI = 100

sayfa_bp = Blueprint('sayfa', __name__)

# DIKKAT: url_prefix burada VERILMEZ.
# Yonerge Modul E, oneki create_app icinde register_blueprint(..., url_prefix='/api')
# ile istiyor. Iki yerde birden yazilirsa yollar /api/api/sohbet olur.
api_bp = Blueprint('api', __name__)


# ---------------------------------------------------------------------------
# Yardimcilar
# ---------------------------------------------------------------------------

def _govde():
    """Istek govdesini sozluk olarak dondurur.

    silent=True sayesinde bozuk JSON gelirse Flask'in HTML hata sayfasi yerine
    bos sozluk doner; boylece asagidaki dogrulamalar devreye girer ve istemci
    her zaman bizim JSON bicimimizi gorur.
    """
    return request.get_json(silent=True) or {}


def _hata(mesaj, kod):
    """Tek bicimli hata yaniti. Her yanitta 'basari' alani bulunur."""
    return jsonify({'basari': False, 'hata': mesaj}), kod


# ---------------------------------------------------------------------------
# Sayfalar
# ---------------------------------------------------------------------------

@sayfa_bp.route('/')
def karsilama():
    """Karsilama sayfasi (B2C): ziyaretci sohbet eder, iletisim birakir."""
    return render_template('index.html')


@sayfa_bp.route('/dashboard')
def panel():
    """Yonetim paneli (B2B): isletme sahibi toplanan kayitlari gorur."""
    return render_template('dashboard.html')


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

@api_bp.route('/sohbet', methods=['POST'])
def sohbet():
    """Ziyaretcinin mesajini yapay zekaya iletir.

    Istek : {"mesaj": "...", "gecmis": [{"role": "...", "content": "..."}]}
    Yanit : {"basari": true, "cevap": "..."}
    """
    veri = _govde()
    mesaj = (veri.get('mesaj') or '').strip()
    gecmis = veri.get('gecmis') or []

    if not mesaj:
        return _hata('Mesaj alani bos olamaz.', 400)

    if len(mesaj) > MESAJ_SINIRI:
        return _hata(f'Mesaj en fazla {MESAJ_SINIRI} karakter olabilir.', 400)

    # gecmis bicimi dogrulanir. Wix tarafi yanlislikla duz metin dizisi
    # gonderirse Groq 400 doner ve biz bunu 503'e cevirirdik -- yanlis teshis.
    # Hatayi kaynaginda yakalamak, hata ayiklamayi saatlerce kisaltir.
    if not isinstance(gecmis, list) or any(
        not isinstance(m, dict) or 'role' not in m or 'content' not in m
        for m in gecmis
    ):
        return _hata(
            "Gecmis bicimi hatali: [{'role': '...', 'content': '...'}] bekleniyor.",
            400,
        )

    try:
        cevap = ai_service.yanit_uret(mesaj, gecmis)
    except AIServiceError as hata:
        # 503 = servis gecici olarak kullanilamiyor. Istemci tekrar deneyebilir.
        # Mesaj ai_service'ten geldigi gibi kullanilir; zaten kibar ve
        # teknik ayrinti icermeyecek sekilde yazilmis.
        return _hata(str(hata), 503)

    return jsonify({'basari': True, 'cevap': cevap})


@api_bp.route('/leads', methods=['POST'])
def lead_kaydet():
    """Yeni bir iletisim kaydi (lead) olusturur.

    Istek : {"isim": "...", "telefon": "...", "mesaj": "..."}
    Yanit : 201 {"basari": true, "lead_id": 7, "mesaj": "Kaydiniz alindi."}
    """
    veri = _govde()
    isim = (veri.get('isim') or '').strip()
    telefon = (veri.get('telefon') or '').strip()
    mesaj = (veri.get('mesaj') or '').strip()

    if not isim or not telefon:
        return _hata('Isim ve telefon alanlari zorunludur.', 400)

    if len(isim) > ALAN_SINIRI or len(telefon) > ALAN_SINIRI:
        return _hata(f'Isim ve telefon en fazla {ALAN_SINIRI} karakter olabilir.', 400)

    # Bos string yerine None kaydedilir; boylece panelde "bos hucre" ile
    # "hic girilmemis" ayrimi veritabani duzeyinde net kalir.
    lead_id = database.lead_ekle(isim, telefon, mesaj or None)

    # 201 = olusturuldu. Yonergenin acikca istedigi durum kodu.
    return jsonify({
        'basari': True,
        'lead_id': lead_id,
        'mesaj': 'Kaydiniz alindi. En kisa surede size donecegiz.',
    }), 201


@api_bp.route('/leads', methods=['GET'])
def leadleri_getir():
    """Butun kayitlari en yeniden eskiye dondurur.

    Yanit : {"basari": true, "adet": 3, "leads": [...]}
    """
    satirlar = database.tum_leadler()

    leads = []
    for satir in satirlar:
        kayit = dict(satir)
        # Wix Repeater bileseni her ogede '_id' alani ZORUNLU tutar ve
        # olmayan veriyi sessizce reddeder (hata vermez, liste bos kalir).
        # Bu alan burada eklenir, database.py'de degil: '_id' bir sunum
        # gereksinimi, veri modelinin parcasi degil.
        kayit['_id'] = str(kayit['id'])
        leads.append(kayit)

    return jsonify({'basari': True, 'adet': len(leads), 'leads': leads})
