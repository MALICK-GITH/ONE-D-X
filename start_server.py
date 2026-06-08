"""
Script de démarrage simple pour le serveur
"""

if __name__ == "__main__":
    import uvicorn
    from simple_server import app
    
    print("🚀 Démarrage du serveur ONE-DELUX-FAST...")
    print("📡 Serveur accessible sur: http://127.0.0.1:8006")
    print("📚 Documentation: http://127.0.0.1:8006/docs")
    print()
    
    uvicorn.run(app, host="127.0.0.1", port=8006)