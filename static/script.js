// script.js

function decomposerIP() {
    const adresseIPInput = document.getElementById("adresse_ip");
    const nombreHotesInput = document.getElementById("nombre_hotes");

    const adresseIP = adresseIPInput.value;
    const nombreHotes = parseInt(nombreHotesInput.value, 10);

    // Vérifier si l'adresse IP existe déjà
    if (ipExists(adresseIP)) {
        document.getElementById("error").innerText = "Adresse IP déjà existante !";
        adresseIPInput.value = "";  // Efface la valeur de la zone de texte
        nombreHotesInput.value = "";  // Efface la valeur du nombre d'hôtes
        return false; // Empêche la soumission du formulaire en cas d'erreur
    }

    // Validation de l'adresse IP
    if (!validateIPAddress(adresseIP)) {
        document.getElementById("error").innerText = "Veuillez entrer une adresse IP valide.";
        adresseIPInput.value = "";  // Efface la valeur de la zone de texte
        nombreHotesInput.value = "";  // Efface la valeur du nombre d'hôtes
        return false;
    }

    // Vérifier si le nombre d'hôtes est un entier valide
    if (isNaN(nombreHotes) || nombreHotes <= 0) {
        document.getElementById("error").innerText = "Veuillez entrer un nombre d'hôtes valide.";
        nombreHotesInput.value = "";  // Efface la valeur du nombre d'hôtes
        return false;
    }

    // ... (le reste du code pour la validation)

    // Réinitialise le message d'erreur s'il est valide
    document.getElementById("error").innerText = "";

    // Soumettre le formulaire
    document.forms[0].submit();
}

// Fonction pour valider une adresse IP (l'expression régulière (ipRegex) pour valider si la saisie correspond à une adresse IP valide. L'expression régulière vérifie si l'adresse IP a le format attendu (xxx.xxx.xxx.xxx))
function validateIPAddress(ip) {
    const ipRegex = /^(\d{1,3}\.){3}\d{1,3}$/;
    return ipRegex.test(ip);
}

function ipExists(ip) {
    // Obtenez toutes les adresses IP existantes de la page
    const existingIPs = document.querySelectorAll('[id^="adresseReseau"]');
    // Vérifiez si l'adresse IP entrée existe déjà
    for (const existingIP of existingIPs) {
        if (existingIP.innerText === ip) {
            return true; // L'adresse IP existe déjà
        }
    }
    return false; // L'adresse IP n'existe pas
}

function editerLigne(ip, nombreHotes) {
    window.location.href = "/editer/" + ip;
}

function supprimerLigne(ipToDelete) {
    // Envoie une requête au serveur Flask pour supprimer l'adresse IP
    fetch('/supprimer/' + ipToDelete, { method: 'GET' })
        .then(response => {
            if (response.ok) {
                // Si la suppression côté serveur réussit, actualise la page pour refléter les modifications
                window.location.reload();
            }
        })
        .catch(error => console.error('Erreur lors de la suppression :', error));
}
