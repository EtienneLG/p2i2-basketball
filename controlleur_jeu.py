from time import perf_counter
from datetime import datetime, timedelta

class ControlleurJeu:
    """
    Classe qui gère les différents états de la partie
    """
    def __init__(self):
        self.bd = None

        self.dernier_score = None
        self.reset()

    def reset(self):
        """
        Initialise les paramètres d'une nouvelle partie
        """
        print("Reset partie")
        self.state = "waituid"

        self.email = None
        self.uid = None
        self.nom = None
        self.prenom = None

        self.partie_lancee = False
        self.debut_temps = None

    def uid_scanned(self, uid):
        """
        Vérifie si l'utilisateur avec l'uid existe déjà dans la BD et s'il n'a pas déjà joué récemment.
        Si oui, lance la partie.
        Sinon, change l'état de la partie en attente d'un email de la parte de l'interface web
        Paramètres:
            uid: uid scanné
        """
        bd_results = self.bd.chercher_utilisateur(uid)
        if len(bd_results) == 0:
            self.uid = uid
            self.state = "askemail"
        else:
            parties_precedentes = self.bd.parties_precedentes(uid)
            if (len(parties_precedentes) > 0 and datetime.now() - parties_precedentes[0][0] > timedelta(seconds=1))\
                    or len(parties_precedentes) == 0:
                self.uid = uid
                self.email = bd_results[0][0] + "@insa-lyon.fr"
                self.nom = bd_results[0][2]
                self.prenom = bd_results[0][3]
                self.lancer()
            else:
                print("TOO MANY")
                self.state = "cancel"

    def enregistrer_score(self, score):
        """
        Enregistre le score de l'utilisateur lors de la partie dans la BD
        Paramètres:
            score: score de la partie
        """
        self.dernier_score = score
        self.bd.ajouter_partie(self.uid, score)
        print(f"--Score de la partie: {score}--\n")

    def enregistrer_utilisateur(self, response):
        """
        Enregistre, grâce à la réponse de l'utilisateur dans l'interface web, un nouvel utilisateur dans la BD
        """
        self.email = response.get('email').replace("@insa-lyon.fr", "")
        self.nom = response.get('nom')
        self.prenom = response.get('prenom')
        self.bd.ajouter_utilisateur(self.email, self.uid, self.nom, self.prenom)

    def timer(self):
        """
        Retourne le temps écoulé depuis le début de la partie
        """
        return datetime.now().timestamp() - self.debut_temps

    def lancer(self):
        """
        Lance une nouvelle partie
        """
        print("\n--Début partie--")
        self.partie_lancee = True
        self.state = "ingame"
        self.debut_temps = datetime.now().timestamp()
    
    def end(self):
        """
        Vérifie si la partie est finie (temps écoulé)
        """
        return self.timer() > 30