"""
run.py  —  Modul E: Giris noktasi

Uygulamayi baslatan dosya. Iki farkli sekilde kullanilir:

  1. Yerelde  :  python run.py
                 Asagidaki __main__ blogu calisir, Flask'in gelistirme
                 sunucusu acilir.

  2. Render'da:  gunicorn run:app
                 gunicorn bu dosyayi import eder ve icindeki 'app'
                 degiskenini arar. __main__ blogu CALISMAZ.
"""

import os

from app import create_app

# 'app' MODUL DUZEYINDE tanimli olmak zorunda.
# 'gunicorn run:app' komutu tam olarak bu ismi ariyor. Asagidaki __main__
# blogunun icine yazilsaydi yerelde calisir, Render'da
# "Failed to find attribute 'app' in 'run'" hatasi verirdi -- ve bu ancak
# dagitim sirasinda fark edilirdi.
app = create_app()


if __name__ == '__main__':
    # PORT ortamdan okunuyor: Render hangi portu dinleyecegini bu degiskenle
    # bildirir. Yerelde tanimli olmadigi icin 5000'e duser.
    port = int(os.environ.get('PORT', 5000))

    # host='0.0.0.0': yalnizca 127.0.0.1 degil, tum arayuzler dinlenir.
    # Render'da bu sart; yerelde de telefondan test etmeye izin verir.
    app.run(host='0.0.0.0', port=port, debug=app.config['DEBUG'])
