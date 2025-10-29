let inGame = false;

function verifierEtat(){
    /*
    Fonction qui vérifie l'état de la partie auprès du script python
    en envoyant des requêtes réguilièrement (toutes les 1 ou 0.5 secondes)
    */
    $.ajax({
        type: 'GET',
        url: '/json/data/state',
        dataType: 'json'
    })
    .done(function(response){
        if (response.state == "waituid") {
            if (inGame) {
                inGame = false;
                changementTrie();
                afficherDernierScore();
                document.getElementById('attenteOverlay').style.display = 'none';
                document.getElementById('timerOverlay').style.display = 'none';
            }
            setTimeout(verifierEtat, 1000);
        } else if (response.state == "askemail") {
            document.getElementById('emailOverlay').style.display = 'flex';
        } else if (response.state == "ingame") {
            if (!inGame) {
                inGame = true;
                lancerUnePartie();
            }
            setTimeout(verifierEtat, 500);
        } else if (response.state == "cancel") {
            alert("Vous avez joué il y a moins d'une heure !");
            setTimeout(verifierEtat, 1000);
        }
    });
}

function changementTrie() {
    const parties = document.getElementById('trieParties').value;
    const ordre = document.getElementById('ordreParties').value;
    console.log(parties);
    if (parties == "mes-parties") {
        document.getElementById('scanOverlay').style.display = 'flex';

        $.ajax({
            type: 'GET',
            url: '/json/data/scanuid',
            dataType: 'json'
        })
        .done(function(response) {
            document.getElementById('scanOverlay').style.display = 'none';
            afficherScores(response.uid, ordre);
        })
    } else {
        afficherScores(undefined, ordre);
    }
}

function afficherDernierScore() {
    /*
    Affiche le dernier score
    */
    $.ajax({
        type: 'GET',
        url: '/json/data/dernierscore',
        dataType: 'json'
    })
    .done(function(response) {
        console.log(response);
        if (response.score != null) {
            document.getElementById('finalScoreOverlay').style.display = 'flex';
            document.getElementById('finalScore').textContent = response.score;
        }
    })
}

function afficherScores(uid=null, ordre="score") {
    /*
    Affiche les scores de toute les parties en les récupérant depuis le script python
    */
    $("#identifiantsTable tbody tr").remove();
    $.ajax({
        type: 'GET',
        url: '/json/data/scores',
        data: {
            uid: uid,
            ordre, ordre
        },
        dataType: 'json'
    })
    .done(function(response) {
        //document.getElementById('attenteOverlay').style.display = 'none';
        for (const s of response.scores) {
            const nom = s[0];
            const prenom = s[1];
            const score = s[2];
            const date = new Date(s[3]);
            const parsedDate = date.toLocaleDateString("fr") + " " + date.toLocaleTimeString('fr-FR');

            addToTable(parsedDate, nom, prenom, score);
        }
    })
}

function validateEmail() {
    /*
    Vérifie l'input de l'utilisateur dans le champs texte et l'envoie au script python en conséquent
    */
    const email = document.getElementById('emailInput').value;
    const confirmation = document.getElementById('confirmation');

    // Vérification de l'email INSA
    const emailRegex = /^([\w\-]+)\.([\w\-]+)$/;

    if (emailRegex.test(email)) {
        confirmation.textContent = "";

        groups = emailRegex.exec(email);
        prenom = titleCase(groups[1].replace("-", " "));
        nom = titleCase(groups[2].replace("-", " "));

        document.getElementById('emailOverlay').style.display = 'none';

        // Communique le nouvel utilisateur au script python
        $.ajax({
            url: '/json/data/validateemail', // URL
            method: 'GET',            // Méthode
            data: {                   // Paramètres
                email: email,
                nom: nom,
                prenom: prenom
            },
            dataType: 'json'          // Type de retour attendu
        }).done(function(response){   // Function appelée lorsque les données arrivent
            console.log("Email communiqué");
            verifierEtat();
        })
    } else {
        confirmation.textContent = "Adresse e-mail invalide.";
        confirmation.style.color = "red";
    }
}

function lancerUnePartie(){
    /*
    Lance le timer de la partie
    */
    document.getElementById('attenteOverlay').style.display = 'flex';
    const overlay = document.getElementById('timerOverlay');
    let timeLeft = 3;
    overlay.style.display = 'flex';
    overlay.textContent = timeLeft;

    overlay.style.backgroundColor = '#008000';
    let jeuLancee = false;
    const interval = setInterval(() => {
        timeLeft--;
        overlay.textContent = timeLeft;
        if (timeLeft == 0) {
            if (!jeuLancee) {
                console.log("Début partie !");
                jeuLancee = true;
                overlay.style.backgroundColor = '#FF0000';
                timeLeft = 30;
                overlay.textContent = timeLeft;
            } else {
                clearInterval(interval);
                overlay.style.display = 'none';
            }
       }
    }, 1000);
}

function addToTable(date, nom, prenom, score) {
    /*
    Ajoute une valeur dans le tableau
    */
    const table = document.getElementById("identifiantsTable").getElementsByTagName('tbody')[0];
    const newRow = table.insertRow();
    newRow.insertCell(0).textContent = date;
    newRow.insertCell(1).textContent = nom;
    newRow.insertCell(2).textContent = prenom;
    newRow.insertCell(3).textContent = score;
}

function titleCase(str) {
    /*
    Modifie la chaine str avec des majuscules au début de chaque mot
    */
    var splitStr = str.toLowerCase().split(' ');
    for (var i = 0; i < splitStr.length; i++) {
        splitStr[i] = splitStr[i].charAt(0).toUpperCase() + splitStr[i].substring(1);
    }
    return splitStr.join(' ');
}

changementTrie();
verifierEtat();