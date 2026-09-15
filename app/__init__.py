# __init__.py - Uygulamayi kuran dosya
# create_app() bir Flask uygulamasi hazirlayip geri dondurur.

import os

from flask import Flask, jsonify
from flask_cors import CORS

from config import config


def create_app(ortam=None):
    uygulama = Flask(__name__)

    # 1) Ayarlar
    if ortam is None:
        ortam = os.environ.get('FLASK_ENV', 'development')
    uygulama.config.from_object(config.get(ortam, config['default']))

    # 2) CORS - Wix baska bir adreste oldugu icin tarayici
    #    normalde istegi engelliyor, burada izin veriyoruz
    kaynaklar = uygulama.config['CORS_ORIGINS'].split(',')
    CORS(uygulama, resources={r'/api/*': {'origins': kaynaklar}})

    # 3) Veritabani - tablo yoksa olusturulsun
    from app.database import init_db
    with uygulama.app_context():
        init_db(uygulama)

    # 4) Rotalar
    # Import burada yapiliyor, dosyanin en ustunde degil.
    # routes.py 'from app import database' yaziyor, yani bu dosyaya
    # geri bakiyor. Ustte import edersek dairesel import hatasi olur.
    from app.routes import api_bp, sayfa_bp
    uygulama.register_blueprint(sayfa_bp)
    uygulama.register_blueprint(api_bp, url_prefix='/api')

    # 5) Sunucu ayakta mi kontrolu. Render dagitiminin
    #    tamamlandigini bu adresle dogruluyoruz.
    @uygulama.route('/health')
    def saglik():
        return jsonify({
            'basari': True,
            'durum': 'aktif',
            'ortam': ortam,
            'ai_saglayici': uygulama.config['AI_PROVIDER'],
            # anahtarin kendisini donmuyoruz, sadece var mi yok mu
            'ai_hazir': bool(uygulama.config['GROQ_API_KEY'])
        })

    return uygulama
