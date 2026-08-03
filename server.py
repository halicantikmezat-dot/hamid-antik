from flask import Flask, render_template, request, jsonify, send_file, url_for
import time
import os
import pandas as pd
import csv
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'mp4', 'mov', 'webm', 'mkv', 'avi'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def dosya_uzantisi_uygun(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

mezat_verisi = {
    "urunler": [
        {
            "id": 1, 
            "lot": 1, 
            "ad": "Osmanlı Gümüş Şamdan", 
            "acilis": 100.0, 
            "hemen_al": 500.0, 
            "guncel_fiyat": 100.0, 
            "fotograflar": [],
            "video": "",
            "tanitim_yazisi": "19. yüzyıl Osmanlı dönemi el işçiliği gümüş kaplama antika şamdan."
        }
    ],
    "satilan_urunler": [],
    "aktif_urun": None,
    "pey": 0.0,
    "kazanan": "Yok",
    "durum": "Bekliyor", 
    "sure_bitis": 0,
    "kayitli_musteriler": [],
    "musteri_pey_listesi": [], # İzleyicilerin verdiği peylerin ve taleplerin tutulduğu ortak liste
    "bildirimler": []
}

if mezat_verisi["urunler"] and not mezat_verisi["aktif_urun"]:
    mezat_verisi["aktif_urun"] = mezat_verisi["urunler"][0]
    mezat_verisi["pey"] = mezat_verisi["aktif_urun"]["guncel_fiyat"]

@app.route('/')
def izleyici():
    return render_template('index.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/durum-getir')
def durum_getir():
    try:
        if mezat_verisi["durum"] == "Sayim":
            kalan = mezat_verisi["sure_bitis"] - time.time()
            if kalan <= 0:
                mezat_verisi["durum"] = "Satıldı"
                if mezat_verisi["aktif_urun"]:
                    satis_fiyati = mezat_verisi["pey"] if mezat_verisi["pey"] > 0 else mezat_verisi["aktif_urun"].get('acilis', 0)
                    kazanan_kisi = mezat_verisi["kazanan"] if mezat_verisi["kazanan"] != "Yok" else "Açık Artırma Alıcısız Kapandı"
                    satilan_id = mezat_verisi["aktif_urun"].get('id')
                    
                    kazanan_adres = "Adres belirtilmedi"
                    for m in mezat_verisi["kayitli_musteriler"]:
                        if m["ad"].lower() in kazanan_kisi.lower():
                            kazanan_adres = m.get("adres", "Adres belirtilmedi")
                            break

                    arsiv_kaydi = {
                        "id": satilan_id,
                        "lot": mezat_verisi["aktif_urun"]["lot"],
                        "ad": mezat_verisi["aktif_urun"]["ad"],
                        "fiyat": satis_fiyati,
                        "alan": kazanan_kisi,
                        "yonetici": "Hamdullah Bulut",
                        "adres": kazanan_adres
                    }
                    
                    if not any(s.get('id') == satilan_id for s in mezat_verisi["satilan_urunler"]):
                        mezat_verisi["satilan_urunler"].append(arsiv_kaydi)
                        
                        # CSV dosyasına kaydetme
                        dosya_adi = "yonetici_satis_arsivi.csv"
                        dosya_var = os.path.exists(dosya_adi)
                        with open(dosya_adi, mode='a', newline='', encoding='utf-8-sig') as f:
                            writer = csv.DictWriter(f, fieldnames=["lot", "ad", "fiyat", "alan", "yonetici"])
                            if not dosya_var:
                                writer.writeheader()
                            writer.writerow({
                                "lot": arsiv_kaydi["lot"],
                                "ad": arsiv_kaydi["ad"],
                                "fiyat": arsiv_kaydi["fiyat"],
                                "alan": arsiv_kaydi["alan"],
                                "yonetici": arsiv_kaydi["yonetici"]
                            })
                    
                    # Sayım bittiğinde ispatlı ve şık tebrik mesajı bildirimi
                    if kazanan_kisi != "Açık Artırma Alıcısız Kapandı":
                        tebrik_bildirimi = f"Tebrikler {kazanan_kisi}! Güzel bir eser kazandınız, iyi günlerde sergileyin. (Lot #{mezat_verisi['aktif_urun']['lot']} - {satis_fiyati} TL)"
                    else:
                        tebrik_bildirimi = f"Lot #{mezat_verisi['aktif_urun']['lot']} alıcısız kapandı."
                        
                    if tebrik_bildirimi not in mezat_verisi["bildirimler"]:
                        mezat_verisi["bildirimler"].insert(0, tebrik_bildirimi)

                    mezat_verisi["urunler"] = [u for u in mezat_verisi["urunler"] if u['id'] != satilan_id]
                    
                    # 🧹 KÖKTEN TEMİZLİK: Satılan ürüne ait eski pey/talep kayıtlarını listeden uçuruyoruz
                    mezat_verisi["musteri_pey_listesi"] = [p for p in mezat_verisi["musteri_pey_listesi"] if p['urun_id'] != satilan_id]
                    
                    mezat_verisi["aktif_urun"] = None
    except Exception as e:
        print("Durum getirme hatası:", e)
        
    return jsonify(mezat_verisi)

@app.route('/kayit-ol', methods=['POST'])
def kayit_ol():
    try:
        data = request.json or {}
        ad = data.get('ad')
        tel = data.get('tel')
        mail = data.get('mail')
        adres = data.get('adres')
        
        if mail and adres:
            musteri = {"ad": ad, "tel": tel, "mail": mail, "adres": adres}
            if musteri not in mezat_verisi["kayitli_musteriler"]:
                mezat_verisi["kayitli_musteriler"].append(musteri)
            return jsonify({"success": True})
        return jsonify({"success": False, "mesaj": "E-posta ve Açık Adres zorunludur!"})
    except Exception as e:
        return jsonify({"success": False, "mesaj": str(e)})

@app.route('/pey-ver', methods=['POST'])
def pey_ver_islem():
    try:
        data = request.json or {}
        urun_id = data.get('urun_id')
        musteri_adi = data.get('musteri_adi', 'Misafir Müşteri')
        eklenen_pey = float(data.get('miktar', 0))
        islem_tipi = data.get('islem', 'pey')

        try:
            urun_id_int = int(urun_id) if urun_id is not None else None
        except:
            urun_id_int = None

        if urun_id_int is not None:
            for satilan in mezat_verisi["satilan_urunler"]:
                if satilan.get('id') == urun_id_int:
                    return jsonify({"success": False, "mesaj": "Bu ürün satılmıştır!"})

        hedef_urun = None
        if urun_id_int is not None:
            for u in mezat_verisi["urunler"]:
                if u['id'] == urun_id_int:
                    hedef_urun = u
                    break
        
        if not hedef_urun and mezat_verisi["aktif_urun"]:
            hedef_urun = mezat_verisi["aktif_urun"]

        if not hedef_urun:
            return jsonify({"success": False, "mesaj": "Geçerli bir ürün bulunamadı!"})

        if islem_tipi == 'talep':
            bildirim_metni = f"{musteri_adi}, Lot #{hedef_urun.get('lot')} - {hedef_urun.get('ad')} ürününü incelemeye aldı."
            if bildirim_metni not in mezat_verisi["bildirimler"]:
                mezat_verisi["bildirimler"].insert(0, bildirim_metni)
            return jsonify({"success": True})

        if mezat_verisi["aktif_urun"] is None or mezat_verisi["aktif_urun"]["id"] != hedef_urun["id"]:
            mezat_verisi["aktif_urun"] = hedef_urun
            mezat_verisi["pey"] = hedef_urun.get('guncel_fiyat', hedef_urun.get('acilis', 100.0))
            mezat_verisi["kazanan"] = "Yok"
            mezat_verisi["durum"] = "Bekliyor"

        if mezat_verisi["durum"] == "Satıldı":
            return jsonify({"success": False, "mesaj": "Bu ürün satılmıştır!"})

        if islem_tipi == 'hemen_al':
            hemen_al_fiyat = hedef_urun.get('hemen_al', hedef_urun.get('guncel_fiyat', 0) * 1.5)
            hedef_urun['guncel_fiyat'] = hemen_al_fiyat
            mezat_verisi["pey"] = hemen_al_fiyat
            mezat_verisi["kazanan"] = musteri_adi + " (HEMEN ALDI!)"
            mezat_verisi["durum"] = "Satıldı"
            
            satilan_id = hedef_urun.get('id')
            kazanan_adres = "Adres belirtilmedi"
            for m in mezat_verisi["kayitli_musteriler"]:
                if m["ad"].lower() in musteri_adi.lower():
                    kazanan_adres = m.get("adres", "Adres belirtilmedi")
                    break

            arsiv_kaydi = {
                "id": satilan_id,
                "lot": hedef_urun['lot'],
                "ad": hedef_urun['ad'],
                "fiyat": mezat_verisi["pey"],
                "alan": mezat_verisi["kazanan"],
                "yonetici": "Hamdullah Bulut",
                "adres": kazanan_adres
            }
            if not any(s.get('id') == satilan_id for s in mezat_verisi["satilan_urunler"]):
                mezat_verisi["satilan_urunler"].append(arsiv_kaydi)
                
                # CSV dosyasına kaydetme
                dosya_adi = "yonetici_satis_arsivi.csv"
                dosya_var = os.path.exists(dosya_adi)
                with open(dosya_adi, mode='a', newline='', encoding='utf-8-sig') as f:
                    writer = csv.DictWriter(f, fieldnames=["lot", "ad", "fiyat", "alan", "yonetici"])
                    if not dosya_var:
                        writer.writeheader()
                    writer.writerow({
                        "lot": arsiv_kaydi["lot"],
                        "ad": arsiv_kaydi["ad"],
                        "fiyat": arsiv_kaydi["fiyat"],
                        "alan": arsiv_kaydi["alan"],
                        "yonetici": arsiv_kaydi["yonetici"]
                    })
            
            mezat_verisi["urunler"] = [u for u in mezat_verisi["urunler"] if u['id'] != satilan_id]
            
            # 🧹 KÖKTEN TEMİZLİK: Hemen al ile satılan ürüne ait eski pey kayıtlarını uçuruyoruz
            mezat_verisi["musteri_pey_listesi"] = [p for p in mezat_verisi["musteri_pey_listesi"] if p['urun_id'] != satilan_id]
            
            mezat_verisi["aktif_urun"] = None

        elif eklenen_pey > 0:
            mezat_verisi["pey"] += eklenen_pey
            hedef_urun['guncel_fiyat'] = mezat_verisi["pey"]
            mezat_verisi["kazanan"] = musteri_adi
            if mezat_verisi["durum"] == "Sayim":
                mezat_verisi["sure_bitis"] = time.time() + 60

        bildirim_metni = f"{musteri_adi}, Lot #{hedef_urun.get('lot')} - {hedef_urun.get('ad')} ürününe {int(mezat_verisi['pey'])} TL pey bıraktı."
        mezat_verisi["bildirimler"].insert(0, bildirim_metni)
        mezat_verisi["musteri_pey_listesi"].insert(0, {
            "urun_id": hedef_urun.get('id'),
            "lot": hedef_urun.get('lot'),
            "urun_adi": hedef_urun.get('ad'),
            "musteri": musteri_adi,
            "fiyat": mezat_verisi["pey"],
            "metin": bildirim_metni
        })

        return jsonify({"success": True, "yeni_pey": mezat_verisi["pey"]})
    except Exception as e:
        return jsonify({"success": False, "mesaj": str(e)})

@app.route('/excel-indir')
def excel_indir():
    try:
        if not mezat_verisi["satilan_urunler"] and not mezat_verisi["kayitli_musteriler"]:
            return "Henüz indirilecek veri bulunmuyor!", 400
        
        dosya_yolu = "mezat_raporu.xlsx"
        with pd.ExcelWriter(dosya_yolu, engine='openpyxl') as writer:
            if mezat_verisi["satilan_urunler"]:
                df_data = [{"Lot No": s.get("lot"), "Ürün Adı": s.get("ad"), "Satış Fiyatı (TL)": s.get("fiyat"), "Alan Müşteri": s.get("alan"), "Müşteri Adresi": s.get("adres")} for s in mezat_verisi["satilan_urunler"]]
                pd.DataFrame(df_data).to_excel(writer, sheet_name='Satilan_Urunler', index=False)

            if mezat_verisi["kayitli_musteriler"]:
                df_m_data = [{"Ad Soyad": m.get("ad"), "Telefon": m.get("tel"), "E-posta": m.get("mail"), "Açık Adres": m.get("adres")} for m in mezat_verisi["kayitli_musteriler"]]
                pd.DataFrame(df_m_data).to_excel(writer, sheet_name='Kayitli_Musteriler', index=False)
        
        return send_file(dosya_yolu, as_attachment=True)
    except Exception as e:
        return str(e), 500

@app.route('/admin-islem', methods=['POST'])
def admin_islem():
    try:
        if request.content_type and 'multipart/form-data' in request.content_type:
            islem = request.form.get('islem')
            if islem == 'urun_ekle':
                max_id = max([u.get('id', 0) for u in mezat_verisi["urunler"] + mezat_verisi["satilan_urunler"]], default=0)
                yeni_id = max_id + 1
                yeni_lot = len(mezat_verisi["urunler"]) + len(mezat_verisi["satilan_urunler"]) + 1
                
                ad = request.form.get('ad')
                acilis = float(request.form.get('acilis', 100))
                hemen_al = float(request.form.get('hemen_al', 500))
                tanitim = request.form.get('tanitim_yazisi', '')

                fotograflar = []
                video_url = ""

                files = request.files.getlist('dosyalar')
                for file in files:
                    if file and dosya_uzantisi_uygun(file.filename):
                        original_filename = secure_filename(file.filename)
                        filename = f"{int(time.time())}_{original_filename}"
                        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        file.save(filepath)
                        dosya_url = f"/static/uploads/{filename}"
                        
                        ext = filename.rsplit('.', 1)[1].lower()
                        if ext in {'mp4', 'mov', 'webm', 'mkv', 'avi'}:
                            video_url = dosya_url
                        else:
                            fotograflar.append(dosya_url)

                mezat_verisi["urunler"].append({
                    "id": yeni_id,
                    "lot": int(request.form.get('lot', yeni_lot)),
                    "ad": ad,
                    "acilis": acilis,
                    "hemen_al": hemen_al,
                    "guncel_fiyat": acilis,
                    "fotograflar": fotograflar,
                    "video": video_url,
                    "tanitim_yazisi": tanitim
                })
            return jsonify({"success": True})

        veri = request.json or {}
        islem = veri.get('islem')
        
        if islem == 'urun_sil':
            sil_id = int(veri.get('urun_id'))
            mezat_verisi["urunler"] = [u for u in mezat_verisi["urunler"] if u['id'] != sil_id]
            mezat_verisi["musteri_pey_listesi"] = [p for p in mezat_verisi["musteri_pey_listesi"] if p['urun_id'] != sil_id]
            if mezat_verisi["aktif_urun"] and mezat_verisi["aktif_urun"]['id'] == sil_id:
                mezat_verisi["aktif_urun"] = None
                mezat_verisi["durum"] = "Bekliyor"
        elif islem == 'sahneye_al':
            s_id = int(veri.get('urun_id'))
            for u in mezat_verisi["urunler"]:
                if u['id'] == s_id:
                    mezat_verisi["aktif_urun"] = u
                    mezat_verisi["pey"] = u['guncel_fiyat']
                    mezat_verisi["kazanan"] = "Yok"
                    mezat_verisi["durum"] = "Bekliyor"
                    break
        elif islem == 'mezat_baslat':
            if mezat_verisi["aktif_urun"]:
                mezat_verisi["durum"] = "Sayim"
                mezat_verisi["sure_bitis"] = time.time() + int(veri.get('saniye', 60))
        elif islem == 'erken_kapat':
            mezat_verisi["durum"] = "Satıldı"
            if mezat_verisi["aktif_urun"]:
                satis_fiyati = mezat_verisi["pey"] if mezat_verisi["pey"] > 0 else mezat_verisi["aktif_urun"].get('acilis', 0)
                kazanan_musteri = mezat_verisi["kazanan"] if mezat_verisi["kazanan"] != "Yok" else "Açık Artırma Alıcısız Kapandı"
                satilan_id = mezat_verisi["aktif_urun"].get('id')
                
                kazanan_adres = "Adres belirtilmedi"
                for m in mezat_verisi["kayitli_musteriler"]:
                    if m["ad"].lower() in kazanan_musteri.lower():
                        kazanan_adres = m.get("adres", "Adres belirtilmedi")
                        break

                arsiv_kaydi = {
                    "id": satilan_id,
                    "lot": mezat_verisi["aktif_urun"].get('lot'),
                    "ad": mezat_verisi["aktif_urun"].get('ad'),
                    "fiyat": satis_fiyati,
                    "alan": kazanan_musteri,
                    "yonetici": "Hamdullah Bulut",
                    "adres": kazanan_adres
                }
                
                if not any(s.get('id') == satilan_id for s in mezat_verisi["satilan_urunler"]):
                    mezat_verisi["satilan_urunler"].append(arsiv_kaydi)
                    
                    # CSV dosyasına kaydetme
                    dosya_adi = "yonetici_satis_arsivi.csv"
                    dosya_var = os.path.exists(dosya_adi)
                    with open(dosya_adi, mode='a', newline='', encoding='utf-8-sig') as f:
                        writer = csv.DictWriter(f, fieldnames=["lot", "ad", "fiyat", "alan", "yonetici"])
                        if not dosya_var:
                            writer.writeheader()
                        writer.writerow({
                            "lot": arsiv_kaydi["lot"],
                            "ad": arsiv_kaydi["ad"],
                            "fiyat": arsiv_kaydi["fiyat"],
                            "alan": arsiv_kaydi["alan"],
                            "yonetici": arsiv_kaydi["yonetici"]
                        })
                
                if kazanan_musteri != "Açık Artırma Alıcısız Kapandı":
                    mesaj_metni = f"Tebrikler {kazanan_musteri}! Güzel bir eser kazandınız, iyi günlerde sergileyin. (Lot #{mezat_verisi['aktif_urun']['lot']} - {satis_fiyati} TL)"
                else:
                    mesaj_metni = f"Lot #{mezat_verisi['aktif_urun']['lot']} alıcısız kapandı."

                if mesaj_metni not in mezat_verisi["bildirimler"]:
                    mezat_verisi["bildirimler"].insert(0, mesaj_metni)
                
                mezat_verisi["urunler"] = [u for u in mezat_verisi["urunler"] if u['id'] != satilan_id]
                
                # 🧹 KÖKTEN TEMİZLİK: Erken kapatmada da satılan ürüne ait eski pey kayıtlarını uçuruyoruz
                mezat_verisi["musteri_pey_listesi"] = [p for p in mezat_verisi["musteri_pey_listesi"] if p['urun_id'] != satilan_id]
                
                mezat_verisi["aktif_urun"] = None
                mezat_verisi["pey"] = 0.0
                mezat_verisi["kazanan"] = "Yok"
                
                return jsonify({"success": True, "mesaj": mesaj_metni})
            return jsonify({"success": False, "mesaj": "Sahnede aktif ürün yok!"})

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "mesaj": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)