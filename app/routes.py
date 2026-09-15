# routes.py - Adresler (rotalar)
# Burada SQL ve yapay zeka cagrisi YOK.
# Gelen veriyi kontrol edip dogru katmana gonderiyoruz.

from flask import Blueprint, jsonify, render_template, request

from app import database
from app.services.ai_service import AIServiceError, ai_service

sayfa_bp = Blueprint('sayfa', __name__)

# '/api' oneki burada degil, __init__.py icinde veriliyor.
# Iki yere birden yazilirsa adres /api/api/sohbet olur.
api_bp = Blueprint('api', __name__)


@sayfa_bp.route('/')
def karsilama():
    return render_template('index.html')


@sayfa_bp.route('/dashboard')
def panel():
    return render_template('dashboard.html')


@api_bp.route('/sohbet', methods=['POST'])
def sohbet():
    # silent=True: govde bozuk JSON ise Flask'in HTML hata sayfasi yerine
    # bos sozluk gelsin, biz kendi JSON hatamizi donelim
    veri = request.get_json(silent=True) or {}
    mesaj = veri.get('mesaj', '').strip()
    gecmis = veri.get('gecmis', [])

    if not mesaj:
        return jsonify({'basari': False, 'hata': 'Mesaj alani bos olamaz.'}), 400

    if len(mesaj) > 2000:
        return jsonify({'basari': False, 'hata': 'Mesaj cok uzun.'}), 400

    # gecmis yanlis bicimde gelirse Groq 400 doner ve biz bunu 503 sanariz.
    # Hatayi burada yakalamak daha dogru.
    if not isinstance(gecmis, list):
        return jsonify({'basari': False, 'hata': 'Gecmis liste olmali.'}), 400

    for eski in gecmis:
        if not isinstance(eski, dict) or 'role' not in eski or 'content' not in eski:
            return jsonify({'basari': False, 'hata': 'Gecmis bicimi hatali.'}), 400

    try:
        cevap = ai_service.yanit_uret(mesaj, gecmis)
    except AIServiceError as hata:
        # 503 = servis simdilik calismiyor, sonra tekrar denenebilir
        return jsonify({'basari': False, 'hata': str(hata)}), 503

    return jsonify({'basari': True, 'cevap': cevap})


@api_bp.route('/leads', methods=['POST'])
def lead_kaydet():
    veri = request.get_json(silent=True) or {}
    isim = veri.get('isim', '').strip()
    telefon = veri.get('telefon', '').strip()
    mesaj = veri.get('mesaj', '').strip()

    if not isim or not telefon:
        return jsonify({'basari': False, 'hata': 'Isim ve telefon zorunludur.'}), 400

    if len(isim) > 100 or len(telefon) > 100:
        return jsonify({'basari': False, 'hata': 'Isim veya telefon cok uzun.'}), 400

    # Bos string yerine None kaydediyoruz
    lead_id = database.lead_ekle(isim, telefon, mesaj or None)

    # 201 = yeni kayit olusturuldu
    return jsonify({
        'basari': True,
        'lead_id': lead_id,
        'mesaj': 'Kaydiniz alindi. En kisa surede size donecegiz.'
    }), 201


@api_bp.route('/leads', methods=['GET'])
def leadleri_getir():
    kayitlar = database.tum_leadler()

    leads = []
    for kayit in kayitlar:
        lead = dict(kayit)
        # Wix'teki Repeater bileseni her kayitta _id alani istiyor,
        # olmazsa listeyi bos gosteriyor
        lead['_id'] = str(lead['id'])
        leads.append(lead)

    return jsonify({'basari': True, 'adet': len(leads), 'leads': leads})
