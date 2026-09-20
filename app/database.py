# database.py - Veritabani islemleri
# Projedeki butun SQL bu dosyada. Baska hicbir dosyada sorgu yok.

import sqlite3
from config import Config

# Veritabani dosyasinin yolu. init_db() calisinca guncellenir.
veritabani_yolu = Config.DATABASE_URL


class VeritabaniError(Exception):
    # routes.py bu hatayi yakalayip kullaniciya JSON donuyor.
    # Boylece sqlite3 hatalari routes.py'ye sizmiyor.
    pass


def get_db():
    # Her cagrida yeni baglanti aciyoruz. gunicorn birden fazla isciyle
    # calistigi icin tek baglantiyi paylasmak hata veriyor.
    baglanti = sqlite3.connect(veritabani_yolu)
    # Bu satir sayesinde satir['isim'] yazabiliyoruz, satir[1] degil
    baglanti.row_factory = sqlite3.Row
    return baglanti


def init_db(app):
    # Tablolar yoksa olusturur. IF NOT EXISTS oldugu icin
    # her acilista calismasi sorun degil, veriyi silmez.
    global veritabani_yolu
    veritabani_yolu = app.config['DATABASE_URL']

    baglanti = get_db()
    try:
        baglanti.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                isim    TEXT NOT NULL,
                telefon TEXT NOT NULL,
                mesaj   TEXT,
                tarih   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Ziyaretcinin asistana sordugu her soru ve alinan cevap.
        # Yonetim panelinde gorunuyor; hangi sorular geliyor, gorulsun diye.
        baglanti.execute("""
            CREATE TABLE IF NOT EXISTS sohbetler (
                id     INTEGER PRIMARY KEY AUTOINCREMENT,
                soru   TEXT NOT NULL,
                cevap  TEXT NOT NULL,
                tarih  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        baglanti.commit()
    except sqlite3.Error:
        raise VeritabaniError('Veritabani hazirlanamadi.')
    finally:
        # Hata olsa da olmasa da baglanti kapansin
        baglanti.close()


def lead_ekle(isim, telefon, mesaj=None):
    # Degerleri sorgunun icine yazmiyoruz, ? ile ayri geciyoruz.
    # Yoksa isim alanina SQL komutu yazan biri tabloyu silebilir.
    baglanti = get_db()
    try:
        imlec = baglanti.execute(
            "INSERT INTO leads (isim, telefon, mesaj) VALUES (?, ?, ?)",
            (isim, telefon, mesaj)
        )
        baglanti.commit()
        return imlec.lastrowid
    except sqlite3.Error:
        raise VeritabaniError('Kayit eklenemedi.')
    finally:
        baglanti.close()


def tum_leadler():
    # En yeni kayit en ustte olsun diye id'ye gore tersten siraliyoruz
    baglanti = get_db()
    try:
        imlec = baglanti.execute(
            "SELECT id, isim, telefon, mesaj, tarih FROM leads ORDER BY id DESC"
        )
        return imlec.fetchall()
    except sqlite3.Error:
        raise VeritabaniError('Kayitlar okunamadi.')
    finally:
        baglanti.close()


def sohbet_ekle(soru, cevap):
    baglanti = get_db()
    try:
        imlec = baglanti.execute(
            "INSERT INTO sohbetler (soru, cevap) VALUES (?, ?)",
            (soru, cevap)
        )
        baglanti.commit()
        return imlec.lastrowid
    except sqlite3.Error:
        raise VeritabaniError('Sohbet kaydedilemedi.')
    finally:
        baglanti.close()


def tum_sohbetler(adet=100):
    # Panelde son konusmalar yeterli; hepsini cekmek gereksiz.
    baglanti = get_db()
    try:
        imlec = baglanti.execute(
            "SELECT id, soru, cevap, tarih FROM sohbetler ORDER BY id DESC LIMIT ?",
            (adet,)
        )
        return imlec.fetchall()
    except sqlite3.Error:
        raise VeritabaniError('Sohbetler okunamadi.')
    finally:
        baglanti.close()
