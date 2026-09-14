"""
database.py  —  Modul B: Veri katmani

Projedeki TEK SQL dosyasi. Yonerge Bolum 3'teki mimari sozlesme:
"database.py disinda HICBIR yerde SQL olmayacak."

Bu yuzden baska hicbir dosyada sqlite3 import edilmez, SELECT/INSERT yazilmaz.
routes.py veri isterse buradaki fonksiyonlari cagirir; sorguyu kendisi kurmaz.

Bu dosya yapay zekayi da bilmez. Tek isi: baglanti acmak, tablo kurmak,
kayit eklemek, kayit okumak.
"""

import sqlite3

from config import Config

# Veritabani dosyasinin yolu.
# init_db(app) cagrildiginda app.config'ten guncellenir; boylece testlerde
# ayri bir dosya kullanilabilir. init_db hic cagrilmazsa Config'teki
# varsayilana duser, yani get_db() Flask olmadan da calisir.
_VERITABANI_YOLU = Config.DATABASE_URL


def get_db():
    """Yeni bir SQLite baglantisi acar ve dondurur.

    Her cagrida YENI baglanti acilir, paylasilan tek baglanti tutulmaz.
    Sebebi: gunicorn uretimde birden fazla isci sureciyle calisir ve SQLite
    baglantilari surecler/is parcaciklari arasinda paylasildiginda
    "SQLite objects created in a thread can only be used in that same thread"
    hatasi verir.

    row_factory = sqlite3.Row satiri, sonuclara sutun adiyla erisilmesini
    saglar: satir['isim'] gibi. Bu olmadan yalnizca satir[1] yazilabilirdi ve
    sutun sirasi degistiginde kod sessizce yanlis veri dondururdu.
    """
    baglanti = sqlite3.connect(_VERITABANI_YOLU)
    baglanti.row_factory = sqlite3.Row
    return baglanti


def init_db(app):
    """'leads' tablosunu yoksa olusturur.

    create_app() icinde, uygulama baglami altinda bir kez cagrilir.
    IF NOT EXISTS sayesinde her aciliste tekrar cagrilmasi zararsizdir --
    mevcut veriyi silmez.
    """
    global _VERITABANI_YOLU
    _VERITABANI_YOLU = app.config['DATABASE_URL']

    baglanti = get_db()
    try:
        baglanti.execute(
            """
            CREATE TABLE IF NOT EXISTS leads (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                isim    TEXT NOT NULL,
                telefon TEXT NOT NULL,
                mesaj   TEXT,
                tarih   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        baglanti.commit()
    finally:
        # Hata olsa da olmasa da baglanti kapanir; acik baglanti birakmak
        # dosya kilidi sorunlarina yol acar.
        baglanti.close()


def lead_ekle(isim, telefon, mesaj=None):
    """Yeni bir lead kaydeder ve olusan kaydin id'sini dondurur.

    DIKKAT -- guvenligin kalbi burasi:
    Degerler sorguya f-string ile GOMULMEZ, '?' yer tutucusuyla ayri gecilir.
    sqlite3 bu degerleri veri olarak isler, SQL komutu olarak degil.

    Yanlis olsaydi soyle yazardik:
        f"INSERT INTO leads (isim) VALUES ('{isim}')"
    ve isim alanina  Ali'); DROP TABLE leads;--  yazan biri tabloyu silerdi.
    Dogru hali asagida: enjeksiyon denemesi duz metin olarak kaydedilir.
    """
    baglanti = get_db()
    try:
        imlec = baglanti.execute(
            "INSERT INTO leads (isim, telefon, mesaj) VALUES (?, ?, ?)",
            (isim, telefon, mesaj),
        )
        baglanti.commit()
        # lastrowid: az once eklenen satirin otomatik artan id'si.
        return imlec.lastrowid
    finally:
        baglanti.close()


def tum_leadler():
    """Butun kayitlari en yeniden en eskiye dogru dondurur.

    ORDER BY id DESC kullanildi; tarih sutunu da var ama ayni saniyede eklenen
    iki kaydin sirasi tarihe gore belirsiz kalirdi. id her zaman artan ve
    benzersiz oldugu icin sirayi kesin belirler.

    Donen deger sqlite3.Row listesidir. Sozluge cevirme isi bu katmanin degil;
    onu routes.py yapar (sunum kaygisi veri katmanina sizmasin diye).
    """
    baglanti = get_db()
    try:
        imlec = baglanti.execute(
            "SELECT id, isim, telefon, mesaj, tarih FROM leads ORDER BY id DESC"
        )
        return imlec.fetchall()
    finally:
        baglanti.close()
