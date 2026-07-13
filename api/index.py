from flask import Flask, request, render_template_string
import sys
import os

# Ana uygulamayı import et
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from eczane import app

# Vercel için handler
def handler(request, context):
    return app(request, context)

# Vercel serverless için
app = app
