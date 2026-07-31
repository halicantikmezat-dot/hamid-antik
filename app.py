import time
from flask import Flask, jsonify, render_template, request

app = Flask(__name__, template_folder='.')

VERITABANI = {
    "urunler": [],
    "aktif_urun": None,
    "pey": 0,
    "kazanan": "Yok",
    "durum": "Bekliyor",
    "sure_bitis": 0,
    "musteri_pey_listesi": [],
}


@app.route("/")
def index():
  return render_template("index.html")


@app.route("/admin")
def admin_paneli():
  return render_template("admin.html")


@app.route("/durum-getir")
def durum_getir():
  if VERITABANI["durum"] == "Sayim":
    kalan = VERITABANI["sure_bitis"] - time.time()
    if kalan <= 0:
      VERITABANI["durum"] = "Bitti"

  return jsonify(VERITABANI)


@app.route("/musteri-teklif", methods=["POST"])
def musteri_teklif():
  veri = request.json
  musteri = veri.get("musteri")
  fiyat = float(veri.get("fiyat", 0))

  if VERITABANI["aktif_urun"]:
    if fiyat > VERITABANI["pey"]:
      VERITABANI["pey"] = fiyat
      VERITABANI["kazanan"] = musteri
      # Listeye ekle
      VERITABANI["musteri_pey_listesi"].insert(
          0,
          {
              "musteri": musteri,
              "fiyat": fiyat,
              "lot": VERITABANI["aktif_urun"]["lot"],
              "urun_ad": VERITABANI["aktif_urun"]["ad"],
          },
      )
      return jsonify({"mesaj": "Teklifiniz başarıyla alındı ve sahneye işlendi!"})
    else:
      return jsonify({"mesaj": "Teklifiniz mevcut fiyattan düşük olamaz!"})
  return jsonify({"mesaj": "Şu an sahnede aktif bir ürün bulunmuyor!"})


@app.route("/admin-islem", methods=["POST"])
def admin_islem():
  veri = request.json
  islem = veri.get("islem")

  if islem == "urun_ekle":
    yeni_id = len(VERITABANI["urunler"]) + 1
    yeni_urun = {
        "id": yeni_id,
        "lot": yeni_id,
        "ad": veri.get("ad"),
        "acilis_fiyat": float(veri.get("acilis", 100)),
        "guncel_fiyat": float(veri.get("acilis", 100)),
        "hemen_al": float(veri.get("hemen_al", 500)),
        "tanitim": veri.get("tanitim_yazisi", ""),
        "fotograflar": veri.get("fotograflar", []),
        "video": veri.get("video", ""),
    }
    VERITABANI["urunler"].append(yeni_urun)

  elif islem == "urun_sil":
    sil_id = int(veri.get("urun_id"))
    VERITABANI["urunler"] = [
        u for u in VERITABANI["urunler"] if u["id"] != sil_id
    ]

  elif islem == "sahneye_al":
    secilen_id = int(veri.get("urun_id"))
    for u in VERITABANI["urunler"]:
      if u["id"] == secilen_id:
        VERITABANI["aktif_urun"] = u
        VERITABANI["pey"] = u["guncel_fiyat"]
        VERITABANI["kazanan"] = "Yok"
        VERITABANI["durum"] = "Bekliyor"
        break

  elif islem == "mezat_baslat":
    saniye = int(veri.get("saniye", 60))
    if VERITABANI["aktif_urun"]:
      VERITABANI["durum"] = "Sayim"
      VERITABANI["sure_bitis"] = time.time() + saniye

  elif islem == "erken_kapat":
    VERITABANI["durum"] = "Bitti"

  return jsonify({"durum": "OK"})


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=5000, debug=True)