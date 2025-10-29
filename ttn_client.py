import paho.mqtt.client as mqtt
from datetime import datetime
import json
from time import sleep
from dateutil.parser import parse


class TTNClient:
    """
    Client assurant la communication avec TTN
    """
    def __init__(self):
        self.partie = None
        self.newbaskets = False
        self.newfautes = False
        self.paquets_basket = []
        self.paquets_fautes = []
        self.prochain_uid = ""

    def connect_to_TTN(self, broker, port, ttn_id, ttn_secret):
        """
        Se connecte au TTN
        Paramètres:
            borker, port, ttn_id, ttn_secret: paramètres de connexion
        """
        self.client = mqtt.Client()
        self.client.username_pw_set(ttn_id, ttn_secret)

        # Connexion à TTN avec les identifiants
        print("Connection à TTN...")
        self.client.connect(broker, port, 60)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.loop_start()

    def choose_devices(self, devices):
        """
        S'abonne aux messages des cartes nécessaires
        Paramètres
            devices: dict des cartes arduino dont on veut récupérer les messages
                sous la forme {nom_carte: fonction_carte}
        """
        self.devices = devices
        for d in self.devices.keys():
            self.client.subscribe(f"v3/projet-insa-lyon-p2i-2-224b@ttn/devices/{d}/up")

    def on_connect(self, client, userdata, flags, rc):
        """
        Fonction appellée lors de la connexion à TTN
        """
        print("Connecté au serveur MQTT")

    def on_message(self, client, userdata, msg):
        """
        Fonction appellée à chaque message reçu
        Paramètres:
            msg: le message reçu
        """
        payload = msg.payload.decode()
        device = msg.topic.split("/")[-2]
        print(f"\n[TTNClient {datetime.now().strftime('%H:%M:%S')} {self.devices[device]}] Message reçu --> {payload}")
        try:
            data = json.loads(msg.payload.decode())["uplink_message"]["decoded_payload"]["msg_ascii_recu"]
            date_reception_ms = int(parse(json.loads(msg.payload.decode())["received_at"]).timestamp()*1000)
        except Exception as e:
            data = e
        print(f"|--data--> {data}\n")


        # Si le message vient de la carte avec le capteur RFID
        if self.devices[device] == "RFID" and len(data) == 20:
            if self.prochain_uid is None:
                self.prochain_uid = data
            elif self.partie.uid is None:
                print("UID scanned !")
                self.partie.uid_scanned(data)

        # Si le message vient de la carte avec le capteur Infrarouge
        if self.devices[device] == "Infrarouge" and self.partie.partie_lancee:
            if self.partie.partie_lancee:
                print("Paniers ajoutés")
                for panier in self.absolute_time_paquet(date_reception_ms, data):
                    self.paquets_basket.append(panier)
                self.newbaskets = True

        # Si le message vient de la carte avec le capteur Ultrasons
        if self.devices[device] == "Ultrasons" and self.partie.partie_lancee:
            if self.partie.partie_lancee:
                print("Fautes ajoutées")
                for faute in self.absolute_time_paquet(date_reception_ms, data):
                    self.paquets_fautes.append(faute)
                self.newfautes = True

    def attendre_prochain_uid(self):
        print("En attente d'un scan...")
        self.prochain_uid = None
        while self.prochain_uid is None:
            sleep(0.5)
        print(f"Scanné ! {self.prochain_uid}")
        return self.prochain_uid

    def absolute_time_paquet(self, date_message_ttn, message_arduino):
        """
        Convertit un temps (en ms) d'un message ttn provenant d'un arduino Infrarouge ou Ultrason, relatif au
        lancement de la carte, en un unix timestamp (en ms)
        Paramètres:
            date_message_ttn : la date du message ttn en ms
            message_arduino : une liste de temps en ms provenant du message arduino
        Retourne:
            adapted_times : une liste de temps en ms unix timestamp
        """
        # temps de la carte arduino depuis son démarrage, le supprime au passage
        relative_time_arduino_ms = int(message_arduino.pop(-1))
        # obtention de la différence de time entre temps relatif arduino et temps de ttn
        delta_time = date_message_ttn - relative_time_arduino_ms
        # pour chaque élement de la liste du message ttn, ajouter le delta_time pour mettre les val de l'arduino sur le même fuseau horaire que ttn
        adapted_times = []
        for i in range(len(message_arduino)) :
            adapted_times.append(message_arduino[i] + delta_time)
        return adapted_times

    def cheating_filter(self, list_basket_cheat, interval_min, interval_max):
        """
        Fonction qui prend en paramètres une liste de deux listes correspondant
        aux détections des deux capteurs durant une même partie. Elle determine si un point a été
        obtenu en trichant et renvoit le nombre de point réel en enlevant ceux où
        le joueur a triché
        Paramètres:
            list_basket_cheat : liste de 2 liste. La première renvoie les moments auxquels
                la balle passe dans le panier.
                                La deuxième renvoie les moments auxquels le capteur de tricherie
                detecte un mouvement
            interval_min : temps minimum nécessaire entre détection du capteur tricherie
                et détection du capteur panier (temps min que la balle arrive)
            interval_max : temps maximum nécessaire entre détection du capteur tricherie
                et détection du capteur panier (temps max que la balle arrive)
        Retourne:
            number_points : le nombre de points réels
        """

        list_basket = list_basket_cheat[0]
        list_cheat = list_basket_cheat[1]

        for time_cheat in list_cheat:
            for time_basket in list_basket:
                if (time_cheat - interval_min) <= time_basket <= (time_cheat + interval_max):
                    list_basket.remove(time_basket)
        number_points = len(list_basket)

        return number_points

    def calcul_nb_mesures_dans_temps(self, debut_partie, paniers, fautes):
        """
        Calcul le nb de paniers et de fautes dans le temps impartis
        Paramètres:
            debut_partie : le début de la partie en ms
            paniers : liste des temps en ms des paniers
            fautes : liste des temps en ms des fautes
        Retourne:
            paniers_dans_les_temps : liste des temps en ms des paniers dans les temps de la partie
            fautes_dans_les_temps : liste des temps en ms des fautes dans les temps de la partie
        """
        paniers_dans_les_temps = []
        fautes_dans_les_temps = []
        for p in paniers:
            if debut_partie < p < debut_partie + 30000:
                paniers_dans_les_temps.append(p)
        for f in fautes:
            if debut_partie < f < debut_partie + 30000:
                fautes_dans_les_temps.append(f)
        return paniers_dans_les_temps, fautes_dans_les_temps

    def score(self):
        """
        Calcule le score en fonction des paquets reçus pendant le temps de jeu
        Retourne:
             score: le score du joueur
        """
        print("Waiting for new packets...")
        self.newbaskets = False
        self.newfautes = False
        while not self.newbaskets or not self.newfautes:
            sleep(0.5)
        print("Waiting ended")

        time_rfid = int(self.partie.debut_temps*1000)
        print(f"Début de la partie : {time_rfid}")
        print(f"Les paniers : {self.paquets_basket}")
        print(f"Les fautes : {self.paquets_fautes}")
        paniers, fautes = self.calcul_nb_mesures_dans_temps(time_rfid, self.paquets_basket, self.paquets_fautes)
        print(f"Après traitement --> Paniers : {paniers} / Fautes : {fautes}")

        score = self.cheating_filter([paniers, fautes], 500, 500)
        print(f'Nombre de points : {score}')

        self.paquets_basket = []
        self.paquets_fautes = []
        return score