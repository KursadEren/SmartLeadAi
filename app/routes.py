# routes.py - Adresler (rotalar)
# Burada SQL ve yapay zeka cagrisi YOK.
# Gelen veriyi kontrol edip dogru katmana gonderiyoruz.

from flask import Blueprint, jsonify, render_template, request

from app import database
from app.database import VeritabaniError
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
    # Sayfayi sunucuda dolduruyoruz: tablo hazir gelsin diye.
    try:
        leadler = [dict(k) for k in database.tum_leadler()]
        sohbetler = [dict(k) for k in database.tum_sohbetler()]
    except VeritabaniError as hata:
        return render_template('dashboard.html', hata=str(hata),
                               leadler=[], sohbetler=[])

    return render_template('dashboard.html', hata=None,
                           leadler=leadler, sohbetler=sohbetler)


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

    # Konusmayi panelde gormek icin kaydediyoruz. Kayit basarisiz olursa
    # ziyaretciye yine de cevap donuyoruz; sohbeti kesmek anlamsiz olurdu.
    try:
        database.sohbet_ekle(mesaj, cevap)
    except VeritabaniError:
        pass

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
    try:
        lead_id = database.lead_ekle(isim, telefon, mesaj or None)
    except VeritabaniError as hata:
        # 500 = sunucu tarafinda bir sorun var
        return jsonify({'basari': False, 'hata': str(hata)}), 500

    # 201 = yeni kayit olusturuldu
    return jsonify({
        'basari': True,
        'lead_id': lead_id,
        'mesaj': 'Kaydiniz alindi. En kisa surede size donecegiz.'
    }), 201


@api_bp.route('/leads', methods=['GET'])
def leadleri_getir():
    try:
        kayitlar = database.tum_leadler()
    except VeritabaniError as hata:
        return jsonify({'basari': False, 'hata': str(hata)}), 500

    leads = []
    for kayit in kayitlar:
        lead = dict(kayit)
        # Wix'teki Repeater bileseni her kayitta _id alani istiyor.
        # Basina 'lead' yaziyoruz: bilesenin hazir sablon satirlari
        # '1', '2', '3' id'lerini kullaniyor, ayni id gelince satiri
        # yeniden olusturmuyor ve onItemReady hic calismiyor.
        lead['_id'] = 'lead' + str(lead['id'])
        leads.append(lead)

    return jsonify({'basari': True, 'adet': len(leads), 'leads': leads})


@api_bp.route('/sohbetler', methods=['GET'])
def sohbetleri_getir():
    try:
        kayitlar = database.tum_sohbetler()
    except VeritabaniError as hata:
        return jsonify({'basari': False, 'hata': str(hata)}), 500

    sohbetler = []
    for kayit in kayitlar:
        satir = dict(kayit)
        satir['_id'] = 'sohbet' + str(satir['id'])
        sohbetler.append(satir)

    return jsonify({'basari': True, 'adet': len(sohbetler), 'sohbetler': sohbetler})
