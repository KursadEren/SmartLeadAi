# run.py - Uygulamayi baslatan dosya
# Yerelde:  python run.py
# Render'da: gunicorn run:app

import os
from app import create_app

# 'app' burada, fonksiyonun disinda olmak zorunda.
# gunicorn run:app komutu tam olarak bu ismi ariyor.
app = create_app()


if __name__ == '__main__':
    # Render hangi portu kullanacagimizi PORT degiskeniyle soyluyor.
    # Yerelde tanimli olmadigi icin 5000 kullanilir.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=app.config['DEBUG'])
