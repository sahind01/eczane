from flask import Flask
import sys
import os

# Ana dizini Python path'e ekle
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# eczane.py'deki app'i import et
from eczane import app as flask_app

# Vercel serverless için WSGI uyumluluğu
# Flask uygulamasını doğrudan export et
app = flask_app

# Vercel serverless ortamı için
if __name__ == "__main__":
    app.run()
