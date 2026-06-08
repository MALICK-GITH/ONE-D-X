"""
Version simplifiée de Flask pour test
"""

from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "<h1>ONE-DELUX-FAST - Flask fonctionne!</h1>"

if __name__ == '__main__':
    print("🚀 Démarrage de Flask simplifié...")
    app.run(debug=True, host='127.0.0.1', port=5000)