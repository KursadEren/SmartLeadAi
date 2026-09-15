# database.py - Veritabani islemleri
# Projedeki butun SQL bu dosyada. Baska hicbir dosyada sorgu yok.

import sqlite3
from config import Config

# Veritabani dosyasinin yolu. init_db() calisinca guncellenir.
veritabani_yolu = Config.DATABASE_URL


def get_db():
    # Her cagrida yeni baglanti aciyoruz. gunicorn birden fazla isciyle
    # calistigi icin tek baglantiyi paylasmak hata veriyor.
    baglanti = sqlite3.connect(veritabani_yolu)
    # Bu satir sayesinde satir['isim'] yazabiliyoruz, satir[1] degil
    baglanti.row_factory = sqlite3.Row
    return baglanti


def init_db(app):
    # Tablo yoksa olusturur. IF NOT EXISTS oldugu icin
    # her acilista calismasi sorun degil, veriyi silmez.
    global veritabani_yolu
    veritabani_yolu = app.config['DATABASE_URL']

    baglanti = get_db()
    baglanti.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            isim    TEXT NOT NULL,
            telefon TEXT NOT NULL,
            mesaj   TEXT,
            tarih   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    baglanti.commit()
    baglanti.close()


def lead_ekle(isim, telefon, mesaj=None):
    # Degerleri sorgunun icine yazmiyoruz, ? ile ayri geciyoruz.
    # Yoksa isim alanina SQL komutu yazan biri tabloyu silebilir.
    baglanti = get_db()
    imlec = baglanti.execute(
        "INSERT INTO leads (isim, telefon, mesaj) VALUES (?, ?, ?)",
        (isim, telefon, mesaj)
    )
    baglanti.commit()
    yeni_id = imlec.lastrowid
    baglanti.close()
    return yeni_id


def tum_leadler():
    # En yeni kayit en ustte olsun diye id'ye gore tersten siraliyoruz
    baglanti = get_db()
    imlec = baglanti.execute(
        "SELECT id, isim, telefon, mesaj, tarih FROM leads ORDER BY id DESC"
    )
    kayitlar = imlec.fetchall()
    baglanti.close()
    return kayitlar
