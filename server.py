from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from mcstatus import JavaServer
import yaml
import os
import base64
import threading
import time
from datetime import datetime

app = Flask(__name__, static_folder='static')
CORS(app)

servers = ["hellmc.net", "minefun.net", "spookmc.net", "mineboom.org", "prismamc.net", "dynamicpvp.net", "akumamc.com"]
data_path = "server_data"
icons_path = "static/icons"

if not os.path.exists(data_path):
    os.makedirs(data_path)

if not os.path.exists(icons_path):
    os.makedirs(icons_path)

def update_server_data():
    server_data = {}
    for ip in servers:
        filepath = f"{data_path}/{ip}.yml"
        
        if os.path.exists(filepath):
            with open(filepath, 'r') as file:
                server_data[ip] = yaml.safe_load(file)
        else:
            server_data[ip] = {"status": "offline", "players": 0, "24h_peak": 0, "record": 0, "last_update": ""}

        try:
            server = JavaServer.lookup(ip)
            status = server.status()
            players = status.players.online
            
            record_players = max(players, server_data[ip].get("record", 0))
            
            current_date = datetime.now().strftime("%Y-%m-%d")
            last_update_date = server_data[ip].get("last_update", "")

            if last_update_date != current_date:
                max_players_24h = players
            else:
                max_players_24h = max(players, server_data[ip].get("24h_peak", 0))
            
            icon_path = f"{icons_path}/{ip}.png"
            if status.favicon:
                icon_data = base64.b64decode(status.favicon.split(",")[1])
                with open(icon_path, "wb") as icon_file:
                    icon_file.write(icon_data)
            else:
                icon_path = None

            server_data[ip] = {
                "status": "online",
                "players": players,
                "24h_peak": max_players_24h,
                "record": record_players,
                "last_update": current_date,
                "icon_path": f"/icons/{ip}.png" if icon_path else None,
            }
        except:
            server_data[ip]["status"] = "offline"
            server_data[ip]["players"] = 0
            server_data[ip]["icon_path"] = None

        with open(filepath, "w") as file:
            yaml.dump(server_data[ip], file)
    return server_data

def background_update():
    """Función para actualizar los datos en segundo plano cada 5 segundos."""
    while True:
        update_server_data()
        time.sleep(5)

@app.route('/servers', methods=['GET'])
def get_servers():
    data = {}
    for ip in servers:
        filepath = f"{data_path}/{ip}.yml"
        if os.path.exists(filepath):
            with open(filepath, 'r') as file:
                data[ip] = yaml.safe_load(file)
        else:
            data[ip] = {"status": "unknown", "players": 0, "24h_peak": 0, "record": 0}
    return jsonify(data)

@app.route('/icons/<filename>')
def get_icon(filename):
    return send_from_directory(icons_path, filename)

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    thread = threading.Thread(target=background_update)
    thread.daemon = True
    thread.start()

    app.run(host='0.0.0.0', port=5000, debug=False)