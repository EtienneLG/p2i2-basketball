from datetime import datetime
import mysql.connector as mysql

class BDClient:
    """
    Client assurant la communication avec la BD
    """
    def __init__(self):
        self.connexion_bd_commune = None

    def connexion_bd(self):
        """
        Initialise la connexion à la DB
        """
        print("[BDClient] Connexion BD...")
        try:
            self.connexion_bd_commune = mysql.connect(
                host='fimi-bd-srv1.insa-lyon.fr',
                port=3306,
                user='G224_B',
                password=open("db-password.txt").read(),
                database='G224_B_BD3'  # si jamais on change de BD faut changer ici
            )
            print("[BDClient] => Connexion a G224_B_BD3 Etablie !")
        except Exception as e:
            print('Erreur connexion à la BD [ERROR]')
            print(e)

    def chercher_utilisateur(self, uid):
        """
        Récupère les utilisateurs de la DB avec l'uid donné
        Paramètres:
            uid: uid à trouver dans la BD
        Retourne:
            result: le résultat, vide si rien trouvé
        """
        result = None
        try:
            idcarte = uid.replace(" ", "")
            cursor = self.connexion_bd_commune.cursor()
            cursor.execute(f'SELECT * FROM Utilisateur WHERE idcarte = "{idcarte}"')
            result = cursor.fetchall()
        except Exception as e:
            print('MySQL [FETCH ERROR]')
            print(e)
        print(f"[BDClient] Utilisateur pour {uid} : {result}")
        return result

    def ajouter_utilisateur(self, email, uid, nom, prenom):
        """
        Ajoute un utilisateur à la DB
        Paramètres:
            email, uid, nom, prenom: les coordonées de l'utilisateur à ajouté
        """
        try:
            idcarte = uid.replace(" ", "")
            cursor = self.connexion_bd_commune.cursor()
            cursor.execute(f"INSERT INTO Utilisateur VALUES (%s, %s, %s, %s)", (email, idcarte, nom, prenom))
            self.connexion_bd_commune.commit()
            print("[BDClient] Nouvel utilisateur ajouté à la DB")
        except Exception as e:
            print('MySQL [INSERTION ERROR]')
            print(e)

    def parties_precedentes(self, uid):
        """
        Retourne les parties déjà jouées par l'utilisateur avec l'uid
        Paramètres:
            uid: uid de l'utilisateur
        Retourne:
            result: la liste des parties dans l'ordre décroissant (plus récente en indice 0)
        """
        result = None
        try:
            idcarte = uid.replace(" ", "")
            cursor = self.connexion_bd_commune.cursor()
            cursor.execute(f'SELECT horodateur FROM Parties WHERE idcarte = "{idcarte}" ORDER BY horodateur DESC')
            result = cursor.fetchall()
        except Exception as e:
            print('MySQL [FETCH ERROR]')
            print(e)
        print(f"[BDClient] Parties pour {uid} : {result}")
        return result

    def recuperer_parties(self, uid, ordre):
        """
        Récupère toutes les parties par ordre de nombre de points décroissants
        """
        result = None
        try:
            order_by = "p.nbpoints" if ordre == "score" else "p.horodateur"
            cursor = self.connexion_bd_commune.cursor()
            if uid:
                idcarte = uid.replace(" ", "")
                cursor.execute("SELECT u.nom, u.prenom, p.nbpoints, p.horodateur FROM Parties p, Utilisateur u "
                               "WHERE u.idcarte = p.idcarte AND u.idcarte = %s ORDER BY %s DESC", [idcarte, order_by])
            else:
                cursor.execute("SELECT u.nom, u.prenom, p.nbpoints, p.horodateur FROM Parties p, Utilisateur u "
                               f"WHERE u.idcarte = p.idcarte ORDER BY {order_by} DESC")
            result = cursor.fetchall()
        except Exception as e:
            print('MySQL [FETCH ERROR]')
            print(e)
        print(f"[BDClient] Parties : {result}")
        return result

    def ajouter_partie(self, uid, nbpoints, idmachine=1):
        """
        Ajoute un partie à la DB
        Paramètres:
            uid, nbpoints, idmachine: les paramètres de la partie
        """
        try:
            idcarte = uid.replace(" ", "")
            current_time = str(datetime.now())
            cursor = self.connexion_bd_commune.cursor()
            cursor.execute(f"INSERT INTO Parties (idcarte, idmachine, nbpoints, horodateur) VALUES (%s, %s, %s, %s)",
                           (idcarte, idmachine, nbpoints, current_time))
            print("[BDClient] Nouvelle partie ajouté à la DB")
            self.connexion_bd_commune.commit()
        except Exception as e:
            print('MySQL [INSERTION ERROR]')
            print(e)