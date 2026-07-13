import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import urllib.parse
import os
import time

# ==================== KONFİGÜRASYON ====================
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# Proxy desteği
PROXY_TEMPLATES = [
    "https://proxy.freecdn.workers.dev/?url={url}",
    "https://bstelevision.com/proxy.php?url={url}",
    "https://hello-world-aged-resonance-fc8f.bokaflix.workers.dev/?apiUrl={url}"
]

custom_proxy = os.environ.get("PROXY")
if custom_proxy:
    PROXY_TEMPLATES.insert(0, custom_proxy)

def safe_get(url, headers, timeout=20):
    """Önce doğrudan istek yapar, başarısız olursa proxy'leri dener."""
    try:
        r = requests.get(url, headers=headers, timeout=timeout)
        r.raise_for_status()
        return r
    except Exception:
        pass

    encoded_url = urllib.parse.quote(url, safe='')
    for template in PROXY_TEMPLATES:
        proxy_url = template.format(url=encoded_url)
        try:
            r = requests.get(proxy_url, headers=headers, timeout=timeout)
            r.raise_for_status()
            return r
        except Exception:
            continue
    return None

def slug_olustur(metin):
    """Türkçe karakterleri slug'a çevir"""
    replacements = {
        'ğ': 'g', 'ü': 'u', 'ş': 's', 'ı': 'i', 
        'ö': 'o', 'ç': 'c', 'Ğ': 'g', 'Ü': 'u', 
        'Ş': 's', 'İ': 'i', 'Ö': 'o', 'Ç': 'c'
    }
    for turkce, ingilizce in replacements.items():
        metin = metin.replace(turkce, ingilizce)
    return metin.lower().replace(' ', '-')

def ilce_verisi_cek(il, ilce):
    """Belirtilen il ve ilçe için nöbetçi eczaneleri çeker"""
    il_slug = slug_olustur(il)
    ilce_slug = slug_olustur(ilce)
    url = f"https://www.eczaneler.gen.tr/nobetci-{il_slug}-{ilce_slug}"
    
    sonuc = {
        "il": il,
        "ilce": ilce,
        "eczaneler": [],
        "hata": False
    }
    
    r = safe_get(url, HEADERS, timeout=15)
    if r is None:
        sonuc["hata"] = True
        return sonuc
    
    try:
        soup = BeautifulSoup(r.text, "html.parser")
        for tr in soup.find_all("tr"):
            span = tr.find("span", class_="isim")
            if not span:
                continue
            
            isim = span.get_text(strip=True)
            adres = ""
            tarif = ""
            telefon = ""
            
            adres_div = tr.find("div", class_="col-lg-6")
            if adres_div:
                adres_parts = []
                for item in adres_div.contents:
                    if isinstance(item, str):
                        adres_parts.append(item.strip())
                adres = " ".join(adres_parts).strip()
                
                tarif_div = adres_div.find("div")
                if tarif_div:
                    tarif = tarif_div.get_text(" ", strip=True)
            
            tel_div = tr.find("div", class_="col-lg-3 py-lg-2")
            if tel_div:
                telefon = tel_div.get_text(" ", strip=True)
            
            maps_query = f"{isim} Eczanesi, {adres}, {ilce}, {il}"
            maps_url = f"https://www.google.com/maps/search/{urllib.parse.quote(maps_query)}"
            
            sonuc["eczaneler"].append({
                "isim": isim,
                "adres": adres,
                "tarif": tarif,
                "telefon": telefon,
                "maps_url": maps_url
            })
    except Exception as e:
        sonuc["hata"] = True
    
    return sonuc

# ==================== HTML OLUŞTURMA ====================
def html_olustur():
    html = f'''<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Türkiye Nöbetçi Eczaneler</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Inter', sans-serif; background: #f1f5f9; min-height: 100vh; }}
        .header {{ background: linear-gradient(135deg, #1e293b, #0f172a); padding: 25px 30px; text-align: center; color: #fff; box-shadow: 0 4px 20px rgba(0,0,0,0.2); position: sticky; top: 0; z-index: 1000; }}
        .header h1 {{ font-size: 2em; font-weight: 800; }}
        .header .tarih-saat {{ display: flex; justify-content: center; gap: 20px; margin-top: 10px; flex-wrap: wrap; }}
        .header .tarih-box {{ background: rgba(255,255,255,0.1); padding: 8px 18px; border-radius: 25px; font-size: 0.9em; color: #94a3b8; }}
        .header .saat-box {{ background: #dc2626; padding: 8px 18px; border-radius: 25px; font-weight: 700; font-family: 'Courier New', monospace; color: #fff; }}
        .header .bilgi-box {{ background: rgba(255,255,255,0.1); padding: 8px 18px; border-radius: 25px; font-size: 0.9em; color: #94a3b8; }}
        .header .bilgi-box span {{ color: #fbbf24; font-weight: 700; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 30px 20px; }}
        
        .arama-kutusu {{ 
            width: 100%; 
            max-width: 700px; 
            margin: 0 auto 30px;
            background: #fff;
            border-radius: 50px;
            padding: 5px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            display: flex;
        }}
        .arama-kutusu input {{ 
            flex: 1;
            padding: 16px 24px;
            border: none;
            background: transparent;
            font-size: 1em;
            font-family: 'Inter', sans-serif;
            outline: none;
        }}
        .arama-kutusu button {{ 
            padding: 14px 30px;
            background: linear-gradient(135deg, #3B82F6, #2563EB);
            color: #fff;
            border: none;
            border-radius: 50px;
            font-weight: 700;
            cursor: pointer;
            transition: 0.3s;
            font-family: 'Inter', sans-serif;
            font-size: 1em;
        }}
        .arama-kutusu button:hover {{ 
            transform: scale(1.02);
            box-shadow: 0 4px 15px rgba(59,130,246,0.4);
        }}
        
        .sonuclar {{ 
            background: #fff;
            border-radius: 16px;
            padding: 30px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            min-height: 400px;
        }}
        .sonuclar .bos-mesaj {{ 
            text-align: center;
            padding: 60px 20px;
            color: #94a3b8;
        }}
        .sonuclar .bos-mesaj i {{ font-size: 4em; display: block; margin-bottom: 20px; opacity: 0.3; }}
        .sonuclar .bos-mesaj h3 {{ font-size: 1.5em; color: #1e293b; margin-bottom: 10px; }}
        
        .ilce-baslik {{ 
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 16px 20px;
            background: linear-gradient(135deg, #f8fafc, #f1f5f9);
            border-radius: 12px;
            margin-bottom: 20px;
        }}
        .ilce-baslik .il-icon {{ 
            width: 40px; 
            height: 40px; 
            border-radius: 50%; 
            display: flex; 
            align-items: center; 
            justify-content: center;
            background: linear-gradient(135deg, #3B82F6, #2563EB);
            color: #fff;
            font-weight: 700;
        }}
        .ilce-baslik .il-bilgi {{ flex: 1; }}
        .ilce-baslik .il-bilgi .il {{ font-size: 0.85em; color: #64748b; }}
        .ilce-baslik .il-bilgi .ilce {{ font-size: 1.3em; font-weight: 700; color: #1e293b; }}
        .ilce-baslik .eczane-sayisi {{ 
            background: #dc2626;
            color: #fff;
            padding: 6px 16px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.9em;
        }}
        
        .eczane-kart {{ 
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 18px 22px;
            margin-bottom: 12px;
            transition: 0.2s;
        }}
        .eczane-kart:hover {{ 
            border-color: #3B82F6;
            box-shadow: 0 2px 12px rgba(59,130,246,0.1);
        }}
        .eczane-kart .eczane-isim {{ 
            font-size: 1.1em; 
            font-weight: 700; 
            color: #1e293b; 
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .eczane-kart .eczane-isim .nokta {{ 
            width: 8px; 
            height: 8px; 
            border-radius: 50%; 
            background: #3B82F6;
            flex-shrink: 0;
        }}
        .eczane-kart .bilgi {{ 
            color: #4b5563; 
            font-size: 0.9em; 
            margin-bottom: 6px; 
            display: flex; 
            align-items: flex-start; 
            gap: 10px; 
            line-height: 1.5;
        }}
        .eczane-kart .bilgi i {{ 
            color: #64748b; 
            width: 16px; 
            margin-top: 2px;
            font-size: 0.9em;
        }}
        .eczane-kart .tarif-box {{ 
            background: #fffbeb; 
            border-left: 3px solid #f59e0b; 
            padding: 10px 14px; 
            border-radius: 0 8px 8px 0; 
            margin: 10px 0; 
            color: #92400e; 
            font-size: 0.88em; 
            line-height: 1.5;
        }}
        .eczane-kart .butonlar {{ 
            display: flex; 
            gap: 8px; 
            flex-wrap: wrap; 
            margin-top: 10px;
        }}
        .btn {{ 
            padding: 8px 18px; 
            border-radius: 20px; 
            font-weight: 600; 
            font-size: 0.82em; 
            text-decoration: none; 
            border: none; 
            cursor: pointer; 
            transition: 0.2s; 
            font-family: 'Inter', sans-serif; 
            display: inline-flex; 
            align-items: center; 
            gap: 6px;
        }}
        .btn-telefon {{ background: #dcfce7; color: #166534; }} 
        .btn-telefon:hover {{ background: #bbf7d0; }}
        .btn-harita {{ background: #dbeafe; color: #1e40af; }} 
        .btn-harita:hover {{ background: #bfdbfe; }}
        
        .yukleniyor {{ 
            text-align: center;
            padding: 60px 20px;
        }}
        .yukleniyor .spinner {{ 
            width: 50px; 
            height: 50px; 
            border: 4px solid #e2e8f0; 
            border-top: 4px solid #3B82F6; 
            border-radius: 50%; 
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }}
        @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
        
        .hata-mesaj {{ 
            text-align: center;
            padding: 40px 20px;
            color: #dc2626;
        }}
        .hata-mesaj i {{ font-size: 3em; display: block; margin-bottom: 15px; }}
        
        .footer {{ 
            text-align: center; 
            padding: 30px 20px; 
            color: #9ca3af; 
            font-size: 0.8em; 
            line-height: 1.8;
        }}
        .footer .acil {{ color: #dc2626; font-weight: 700; }}
        
        @media (max-width: 600px) {{ 
            .header h1 {{ font-size: 1.4em; }}
            .arama-kutusu {{ flex-direction: column; border-radius: 20px; padding: 10px; }}
            .arama-kutusu input {{ padding: 12px 16px; }}
            .arama-kutusu button {{ border-radius: 20px; padding: 12px; }}
            .sonuclar {{ padding: 16px; }}
            .eczane-kart {{ padding: 14px 16px; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>💊 Türkiye Nöbetçi Eczaneler</h1>
        <div class="tarih-saat">
            <div class="tarih-box">📅 {datetime.now().strftime("%d.%m.%Y")}</div>
            <div class="saat-box" id="anaSaat">--:--:--</div>
            <div class="bilgi-box">🔍 İl veya ilçe adı yazın</div>
        </div>
    </div>
    <div class="container">
        <div class="arama-kutusu">
            <input type="text" id="aramaInput" placeholder="🔍 İl veya ilçe adı yazın (örn: İstanbul, Kadıköy, Mardin...)" onkeypress="if(event.key==='Enter') aramaYap()">
            <button onclick="aramaYap()"><i class="fas fa-search"></i> Ara</button>
        </div>
        <div class="sonuclar" id="sonuclar">
            <div class="bos-mesaj">
                <i class="fas fa-search"></i>
                <h3>Nöbetçi Eczane Ara</h3>
                <p>Yukarıdaki arama kutusuna il veya ilçe adı yazın.<br>Örnek: İstanbul, Kadıköy, Ankara, Çankaya, İzmir, Mardin...</p>
            </div>
        </div>
    </div>
    <div class="footer">
        <p>Veriler eczaneler.gen.tr üzerinden anlık olarak alınmaktadır.</p>
        <p class="acil">⚠️ Acil durumlarda 112'yi arayınız.</p>
    </div>
    <script>
        function saatGuncelle() {{
            var s = new Date();
            var el = document.getElementById('anaSaat');
            if(el) el.textContent = s.toLocaleTimeString('tr-TR', {{hour:'2-digit', minute:'2-digit', second:'2-digit'}});
        }}
        setInterval(saatGuncelle, 200);
        saatGuncelle();
        
        function aramaYap() {{
            var input = document.getElementById('aramaInput');
            var deger = input.value.trim();
            if (!deger) {{
                document.getElementById('sonuclar').innerHTML = \`
                    <div class="bos-mesaj">
                        <i class="fas fa-search"></i>
                        <h3>Lütfen bir il veya ilçe adı yazın</h3>
                        <p>Örnek: İstanbul, Kadıköy, Ankara, Çankaya, İzmir, Mardin...</p>
                    </div>
                \`;
                return;
            }}
            
            // Yükleniyor göster
            document.getElementById('sonuclar').innerHTML = \`
                <div class="yukleniyor">
                    <div class="spinner"></div>
                    <p style="color: #64748b;">\${deger} için aranıyor...</p>
                </div>
            \`;
            
            // AJAX ile sunucuya gönder
            var xhr = new XMLHttpRequest();
            xhr.open('POST', '/ara', true);
            xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
            xhr.onload = function() {{
                if (this.status == 200) {{
                    document.getElementById('sonuclar').innerHTML = this.responseText;
                }} else {{
                    document.getElementById('sonuclar').innerHTML = \`
                        <div class="hata-mesaj">
                            <i class="fas fa-exclamation-circle"></i>
                            <h3>Bir hata oluştu</h3>
                            <p>Lütfen tekrar deneyin.</p>
                        </div>
                    \`;
                }}
            }};
            xhr.send('q=' + encodeURIComponent(deger));
        }}
    </script>
</body>
</html>'''
    return html

# ==================== WEB SUNUCUSU ====================
from flask import Flask, request, render_template_string

app = Flask(__name__)

@app.route('/')
def index():
    return html_olustur()

@app.route('/ara', methods=['POST'])
def ara():
    sorgu = request.form.get('q', '').strip()
    if not sorgu:
        return '<div class="bos-mesaj"><i class="fas fa-search"></i><h3>Lütfen bir arama yapın</h3></div>'
    
    # İl veya ilçe olarak dene
    sonuc_html = f'<div style="padding: 10px 0;"><div class="ilce-baslik"><div class="il-icon"><i class="fas fa-map-marker-alt"></i></div><div class="il-bilgi"><div class="il">{sorgu}</div><div class="ilce">Aranıyor...</div></div></div></div>'
    
    # Önce il olarak dene
    veri = ilce_verisi_cek(sorgu, "merkez")
    if not veri["hata"] and len(veri["eczaneler"]) > 0:
        return sonuc_olustur(veri)
    
    # İlçe olarak dene - tüm illeri tara (sadece eşleşen ilçeyi bulmak için)
    # Not: Bu kısım performans için optimize edildi - sadece aranan ilçeyi bulmaya çalışır
    # Gerçek kullanımda tüm illeri taramak yerine, yaygın iller için hızlı arama yapılabilir
    
    # Hızlı arama: En yaygın 10 ilde ara
    yaygin_iller = ["İstanbul", "Ankara", "İzmir", "Bursa", "Antalya", "Adana", "Konya", "Gaziantep", "Mersin", "Kocaeli", "Mardin"]
    for il in yaygin_iller:
        veri = ilce_verisi_cek(il, sorgu)
        if not veri["hata"] and len(veri["eczaneler"]) > 0:
            return sonuc_olustur(veri)
    
    # Hiçbir sonuç yoksa
    return f'''
    <div class="bos-mesaj">
        <i class="fas fa-map-marked-alt"></i>
        <h3>"{{sorgu}}" için sonuç bulunamadı</h3>
        <p>Lütfen geçerli bir il veya ilçe adı yazın.</p>
        <p style="font-size: 0.85em; color: #94a3b8; margin-top: 10px;">
            Örnekler: İstanbul, Kadıköy, Ankara, Çankaya, İzmir, Mardin...
        </p>
    </div>
    '''

def sonuc_olustur(veri):
    if veri["hata"] or len(veri["eczaneler"]) == 0:
        return f'''
        <div class="bos-mesaj">
            <i class="fas fa-sad-tear"></i>
            <h3>"{veri['ilce']}" için nöbetçi eczane yok</h3>
            <p>Bugün bu ilçede nöbetçi eczane bulunmamaktadır.</p>
        </div>
        '''
    
    html = f'''
    <div class="ilce-baslik">
        <div class="il-icon"><i class="fas fa-map-marker-alt"></i></div>
        <div class="il-bilgi">
            <div class="il">{veri['il']}</div>
            <div class="ilce">{veri['ilce']}</div>
        </div>
        <div class="eczane-sayisi">{len(veri['eczaneler'])} Nöbetçi Eczane</div>
    </div>
    '''
    
    renkler = ["#3B82F6", "#EF4444", "#10B981", "#F59E0B", "#8B5CF6", "#EC4899", "#14B8A6", "#F97316"]
    renk_indeks = 0
    
    for eczane in veri["eczaneler"]:
        renk = renkler[renk_indeks % len(renkler)]
        renk_indeks += 1
        
        html += f'''
        <div class="eczane-kart">
            <div class="eczane-isim">
                <span class="nokta" style="background: {renk};"></span>
                {eczane['isim']}
            </div>
        '''
        if eczane.get('adres'):
            html += f'<div class="bilgi"><i class="fas fa-map-marker-alt"></i> {eczane["adres"]}</div>'
        if eczane.get('tarif'):
            html += f'<div class="tarif-box">🧭 <strong>Tarif:</strong> {eczane["tarif"]}</div>'
        html += '<div class="butonlar">'
        if eczane.get('telefon'):
            telefon = eczane['telefon'].replace(' ', '').replace('-', '')
            html += f'<a href="tel:{telefon}" class="btn btn-telefon"><i class="fas fa-phone-alt"></i> Ara</a>'
        if eczane.get('maps_url'):
            html += f'<a href="{eczane["maps_url"]}" target="_blank" class="btn btn-harita"><i class="fas fa-map-marked-alt"></i> Harita</a>'
        html += '</div></div>'
    
    return html

# ==================== ANA PROGRAM ====================
if __name__ == "__main__":
    print("=" * 60)
    print("  TÜRKİYE NÖBETÇİ ECZANE ARAMA")
    print("=" * 60)
    print("  🌐 Sunucu başlatılıyor...")
    print("  📱 Tarayıcıda http://127.0.0.1:5000 adresini açın")
    print("  🔍 İl veya ilçe adı yazarak arama yapın")
    print("  ⏹️ Durdurmak için CTRL+C")
    print("=" * 60)
    
    app.run(debug=False, host='0.0.0.0', port=5000)
