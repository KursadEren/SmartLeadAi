"""
__init__.py  —  Modul E: Uygulama fabrikasi

create_app() bir Flask uygulamasi kurup dondurur. "Fabrika" deseninin sebebi:
uygulama modul yuklenirken degil, cagrildiginda olusur. Boylece ayni kodla
farkli ayarlarla (gelistirme / uretim / test) birden fazla uygulama uretilebilir.

Bu dosyada is mantigi YOK -- yalnizca kurulum adimlari ve /health.
Rotalar routes.py'de, SQL database.py'de, yapay zeka ai_service.py'de.
"""

import os

from flask import Flask, jsonify
from flask_cors import CORS

from config import config


def create_app(ortam=None):
    """Uygulamayi kurar ve dondurur.

    Adim sirasi yonergede belirtildigi gibi:
    ayarlari yukle -> CORS ac -> init_db() -> blueprint'leri kaydet -> dondur
    """
    # __name__ burada 'app' paketidir; Flask sablon klasorunu bu sayede
    # kendiliginden app/templates olarak bulur, ayrica ayar gerekmez.
    uygulama = Flask(__name__)

    # --- 1) Ayarlar --------------------------------------------------------
    # Oncelik: fonksiyona verilen deger > FLASK_ENV > 'development'
    ortam = ortam or os.environ.get('FLASK_ENV', 'development')
    # config.get(...) kullanildi: tanimsiz bir ortam adi gelirse coker degil,
    # 'default' sinifina duser.
    uygulama.config.from_object(config.get(ortam, config['default']))

    # --- 2) CORS -----------------------------------------------------------
    # Tarayici, farkli bir alan adindaki sayfanin (Wix) bu sunucuya istek
    # atmasina varsayilan olarak izin vermez. CORS bu izni verir.
    # Yalnizca /api/* yoluna aciliyor; HTML sayfalarinin buna ihtiyaci yok.
    kaynaklar = [k.strip() for k in uygulama.config['CORS_ORIGINS'].split(',')]
    CORS(uygulama, resources={r'/api/*': {'origins': kaynaklar}})

    # --- 3) Veritabani -----------------------------------------------------
    # app_context() icinde cagriliyor: init_db, uygulama ayarlarindan
    # DATABASE_URL okuyor ve bu ancak uygulama baglami altinda guvenli.
    from app.database import init_db
    with uygulama.app_context():
        init_db(uygulama)

    # --- 4) Blueprint'ler --------------------------------------------------
    # Import burada, fonksiyon icinde yapiliyor: routes.py 'from app import
    # database' yaziyor, yani app paketine geri bakiyor. Dosyanin en ustunde
    # import edilseydi dairesel import olusurdu.
    from app.routes import api_bp, sayfa_bp

    uygulama.register_blueprint(sayfa_bp)
    # '/api' oneki TAM OLARAK burada veriliyor, Blueprint tanimda degil.
    uygulama.register_blueprint(api_bp, url_prefix='/api')

    # --- 5) Saglik kontrolu ------------------------------------------------
    @uygulama.route('/health')
    def saglik():
        """Sunucunun ayakta olup olmadigini soyler.

        Render dagitiminin 'tamamlandi' sayilmasi bu uc noktanin yanit
        vermesine bagli (yonerge Modul H).

        DIKKAT: API anahtarinin kendisi asla donmez; yalnizca var/yok bilgisi.
        """
        return jsonify({
            'basari': True,
            'durum': 'aktif',
            'ortam': ortam,
            'ai_saglayici': uygulama.config['AI_PROVIDER'],
            'ai_hazir': bool(uygulama.config['GROQ_API_KEY']),
        })

    return uygulama
