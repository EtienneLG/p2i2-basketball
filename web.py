##--## Fichier à executer pour l'interface web ##--##
# (Garder l'arborescence) #

from ttn_client import TTNClient
from bd_client import BDClient
from controlleur_jeu import ControlleurJeu
from flask import Flask, redirect, jsonify, request


broker = "eu1.cloud.thethings.network"
port = 1883
ttn_application_id = "projet-insa-lyon-p2i-2-224b@ttn"
ttn_api_key_secret = open("api-key.txt").read()

partie = ControlleurJeu()

# Flask Application
app = Flask(__name__)

# MQTT Client
mqtt_client = TTNClient()

# BD client
mysql_client = BDClient()


@app.route("/")
def index():
    return redirect('/static/index.html')


@app.route("/favicon.ico")
def favicon():
    return redirect('/static/img/basketball.ico')


@app.route("/json/data/<query>", methods=['GET'])
def json_handle(query):
    # Renvoie l'état de la partie (waituid, askemail, ingame)
    if query == 'state':
        state = partie.state
        if partie.state == "ingame":
            if partie.end():
                partie.enregistrer_score(mqtt_client.score())
                partie.reset()
        if partie.state == "cancel":
            partie.reset()
        return jsonify({"state": state})

    # Lorsque l'utilisateur valide son email
    if query == 'validateemail':
        partie.enregistrer_utilisateur(request.args)
        partie.lancer()
        return jsonify({"state": "emailReceived"})

    # Retourne tout les scores
    if query == 'scanuid':
        uid = mqtt_client.attendre_prochain_uid()
        return jsonify({"uid": uid})

    # Retourne tout les scores
    if query == 'scores':
        uid = request.args.get("uid")
        ordre = request.args.get("ordre")
        scores = mysql_client.recuperer_parties(uid=uid, ordre=ordre)
        return jsonify({"scores": scores})

    # Retourne le dernier score
    if query == 'dernierscore':
        print(partie.dernier_score)
        return jsonify({"score": partie.dernier_score})


if __name__ == "__main__":
    # Démarre une application web et initialise les clients ttn et sql
    print('Démarrage de l\'application')
    mysql_client.connexion_bd()

    mqtt_client.connect_to_TTN(broker, port, ttn_application_id, ttn_api_key_secret)
    mqtt_client.choose_devices({"g224b-n3": "RFID", "g224b-1": "Infrarouge", "g224b-2": "Ultrasons"})
    mqtt_client.partie = partie
    partie.bd = mysql_client

    app.run(host="127.0.0.1", port=8080, debug=False)
    print('Fin de l\'application')