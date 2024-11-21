from flask import Flask, render_template, request, g, redirect, url_for, Response
import sqlite3
import ipaddress

app = Flask(__name__, static_folder='static')
app.config['DATABASE'] = 'adresse_ip.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(app.config['DATABASE'])
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def create_table():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS adresse_ip (
            id INTEGER PRIMARY KEY,
            adresse TEXT UNIQUE,
            nombre_hotes INTEGER
        )
    ''')
    db.commit()

def insert_ip_address(ip, nombre_hotes):
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("INSERT INTO adresse_ip (adresse, nombre_hotes) VALUES (?, ?)", (ip, nombre_hotes))
        db.commit()
    except sqlite3.IntegrityError:
        db.rollback()  # Adresse IP déjà présente dans la base de données
        
def fetch_ip_addresses():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, adresse, nombre_hotes FROM adresse_ip")
    rows = cursor.fetchall()
    return rows

def decomposer_en_sous_reseaux(ip_base, nombre_hotes, single_address=False):
    try:
        reseau = ipaddress.IPv4Network(ip_base, strict=False)
    except ipaddress.AddressValueError:
        return []  # Retourne une liste vide en cas d'adresse IP incorrecte
    nombre_hotes_necessaires = nombre_hotes + 2
    results = []
    for sous_reseau in reseau.subnets(new_prefix=32):
        masque_sous_reseau = obtenir_masque(str(sous_reseau.network_address))
        adresses_disponibles = list(sous_reseau.hosts())
        if nombre_hotes_necessaires > len(adresses_disponibles):
            adresses_utilisees = adresses_disponibles
        else:
            adresses_utilisees = adresses_disponibles[:nombre_hotes_necessaires]
        i = 1
        for adresse in adresses_utilisees:
            adresse_diffusion = str(adresse + (2 ** (32 - masque_sous_reseau) - 1))
            result = {
                "numero": i,
                "masque_sous_reseau": f"/{masque_sous_reseau}",
                "adresse_reseau": str(sous_reseau.network_address),
                "adresse_diffusion": adresse_diffusion,
                "premiere_adresse": str(adresse + 1),
                "derniere_adresse": str(adresse + nombre_hotes),
                "adresses_disponibles": nombre_hotes,
            }
            results.append(result)
            i += 1
    return results


def obtenir_masque(adresse_ip):
    try:
        ip_obj = ipaddress.IPv4Address(adresse_ip)
    except ipaddress.AddressValueError:
        return None
    reseau = ipaddress.IPv4Network(ip_obj, strict=False)
    return reseau.prefixlen

def obtenir_configuration(ip, masque):
    configuration = f"""
    interface FastEthernet0/0
    ip address {ip}/{masque}
    description Configuration pour l'adresse IP {ip}
    """
    return configuration

@app.route('/')
@app.route('/templates/accueil.html')
def accueil():
    return render_template('accueil.html')

@app.route('/decomposer_ip', methods=['POST'])
def decomposer_ip():
    if request.method == 'POST':
        ip = request.form['adresse_ip']
        nombre_hotes = int(request.form['nombre_hotes'])
        insert_ip_address(ip, nombre_hotes)
        return redirect(url_for('index'))

@app.route('/templates/index.html', methods=['GET'])
def index():
    create_table()
    ip_addresses = fetch_ip_addresses()
    results = []
    for ip_row in ip_addresses:
        ip_base = ip_row[1]
        nombre_hotes = ip_row[2]
        results.extend(decomposer_en_sous_reseaux(ip_base, nombre_hotes))
    return render_template('index.html', results=results)

@app.route('/editer/<ip>', methods=['GET'])
def editer_ip(ip):
    return render_template('editer.html', adresse_ip=ip)

@app.route('/enregistrer_edition/<ip>', methods=['POST'])
def enregistrer_edition(ip):
    nouveau_nombre_hotes = int(request.form['nouveau_nombre_hotes'])
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE adresse_ip SET nombre_hotes = ? WHERE adresse = ?", (nouveau_nombre_hotes, ip))
    db.commit()
    return redirect(url_for('index'))

@app.route('/supprimer/<ip>', methods=['GET'])
def supprimer_ip(ip):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM adresse_ip WHERE adresse = ?", (ip,))
    db.commit()
    return redirect(url_for('index'))

@app.route('/afficher_base_de_donnees', methods=['GET'])
def afficher_base_de_donnees():
    db = get_db()
    cursor = db.cursor()
    table_name = 'adresse_ip'
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    print(f"Table: {table_name}")
    for row in rows:
        id, adresse_ip, nombre_hotes = row
        print(f"(ID = {id}, adresse IP = '{adresse_ip}', nombre d'hôtes = {nombre_hotes})")
    return "Les données de la base de données ont été affichées dans le terminal."

@app.route('/exporter_config/<ip>', methods=['GET'])
def exporter_configuration(ip):
    masque_sous_reseau = obtenir_masque(ip)
    configuration = obtenir_configuration(ip, masque_sous_reseau)
    if configuration:
        return Response(configuration, content_type='text/plain')
    else:
        return "Configuration non trouvée pour l'adresse IP spécifiée.", 404

if __name__ == '__main__':
    app.run(debug=True)
