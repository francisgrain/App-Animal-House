import io
import os
import pandas as pd
from builtins import *
from flask import Flask, request, redirect, url_for, session, render_template, Response, flash, make_response, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf.csrf import CSRFProtect
import mysql.connector
from matplotlib import pyplot as plt
import logging

from wx.lib.agw.hypertreelist import method

# Utilizzo delle variabili d'ambiente per credenziali sensibili
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'default_secret_key')
csrf = CSRFProtect(app)

# Connessione sicura al database
mydb = mysql.connector.connect(
    host=os.environ.get('DB_HOST', 'localhost'),
    user=os.environ.get('DB_USER', 'root'),
    password=os.environ.get('DB_PASS', 'Contananne_2024!'),
    database=os.environ.get('DB_NAME', 'PyDb')
)

'''
mydb1 = mysql.connector.connect(
    host=os.environ.get('DB_HOST', 'localhost'),
    user=os.environ.get('DB_USER', 'root'),
    password=os.environ.get('DB_PASS', 'Contananne_2024!'),
    database=os.environ.get('DB_NAME', 'PyDb')
)
'''


# Classe prodotti
class Prodotti:
    def __init__(self, nome, marca, descrizione, prezzo, categoria, url, pezzi, pezziVenduti, url2=None, url3=None,
                 url4=None):
        self.nome = nome
        self.marca = marca
        self.descrizione = descrizione
        self.prezzo = prezzo
        self.categoria = categoria
        self.url = url
        self.pezzi = pezzi
        self.pezziVenduti = pezziVenduti
        self.url2 = url2  # Nuova immagine
        self.url3 = url3  # Nuova immagine
        self.url4 = url4  # Nuova immagine

    def __str__(self):
        return f"{self.nome}, {self.marca}, {self.descrizione} {self.prezzo}, {self.categoria}, {self.url}, {self.pezzi}, {self.pezziVenduti}, {self.url2}, {self.url3}, {self.url4}"


# Gestione login sicuro con hashing della password
USERNAME = "admin"
PASSWORD_HASH = generate_password_hash("password", method='pbkdf2:sha256')  # Corretto metodo di hashing


@app.route('/')
def home():
    return redirect(url_for('login'))


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Verifica le credenziali dell'utente
        if username == USERNAME and check_password_hash(PASSWORD_HASH, password):
            session['user'] = username  # Memorizza l'utente nella sessione
            return redirect(url_for('gestore'))  # Reindirizza all'area protetta
        else:
            flash("Credenziali non valide", "error")

    return render_template("login.html")


@app.route('/gestore')
def gestore():
    if 'user' not in session:
        return redirect(url_for('login'))

    try:
        mycursor = mydb.cursor()  # Usa un solo cursore per tutto
        mycursor.execute("SELECT * FROM prodottipets")
        myresult = mycursor.fetchall()
        listaD = [i[2] for i in myresult]
        listaS = list(dict.fromkeys(listaD))

        # Utilizzo della libreria pandas
        query = "SELECT * FROM prodottipets"
        df = pd.read_sql(query, mydb)
        pd.set_option('display.max_columns', None)
        lista_prodotti = df.values.tolist()

        # Ottenere i dati per le statistiche
        query = "SELECT id, nome, marca, pezzi, pezziVenduti FROM prodottipets"
        mycursor.execute(query)
        myresult1 = mycursor.fetchall()
        column_names = [desc[0] for desc in mycursor.description]
        df = pd.DataFrame(myresult1, columns=column_names)

        # Somme e medie
        sommaP = round(df['pezzi'].sum())
        sommaV = df['pezziVenduti'].sum()
        mediaP = round(df['pezzi'].mean())
        mediaPv = round(df['pezziVenduti'].mean())

        # Aggiungi righe di somma e media al dataframe
        new_row = {'id': "", 'nome': "SOMMA:", 'marca': "", 'pezzi': sommaP, 'pezziVenduti': sommaV}
        new_row2 = {'id': "", 'nome': "MEDIA:", 'marca': "", 'pezzi': mediaP, 'pezziVenduti': mediaPv}
        df = pd.concat([df, pd.DataFrame([new_row]), pd.DataFrame([new_row2])], ignore_index=True)
        lista_prodotti = df.values.tolist()

        # Trova il prodotto più venduto
        index_max = df['pezziVenduti'][:-2].idxmax()  # Escludi le ultime righe di somma/media
        prodotto_piu_venduto = df.loc[index_max]
        prodottoMax = prodotto_piu_venduto['nome']

        # Trova il prodotto meno venduto
        index_min = df['pezziVenduti'][:-2].idxmin()
        prodotto_meno_venduto = df.loc[index_min]
        prodottoMin = prodotto_meno_venduto['nome']
        # print(prodottoMax)
        # print(prodottoMin)
        mycursor.close()  # Chiudi il cursore correttamente

        return render_template("gestore.html", lista=myresult, listaS=listaS, listaPr=lista_prodotti,
                               prodottoMax=prodottoMax, prodottoMin=prodottoMin)

    except mysql.connector.Error as err:
        flash(f"Errore database: {err}", "error")
        return redirect(url_for('home'))


@app.route('/download_csv')
def download_csv():
    mycursor = mydb.cursor()

    try:
        mycursor.execute("SELECT * FROM prodottipets")
        myresult = mycursor.fetchall()

        def generate():
            yield 'ID - Nome - Marca - Descrizione - Prezzo - Categoria - URL - Pezzi\n'
            for row in myresult:
                yield '-'.join(map(str, row)) + '\n'

        return Response(generate(), mimetype='text/csv', headers={
            'Content-Disposition': 'attachment; filename=prodotti.csv'
        })

    except mysql.connector.Error as err:
        flash(f"Errore database: {err}", "error")
        return redirect(url_for('home'))


@app.route('/magazzino')
def magazzino():
    mycursor = mydb.cursor()

    try:
        mycursor.execute("SELECT * FROM prodottipets")
        myresult = mycursor.fetchall()
        listaD = [i[2] for i in myresult]
        listaS = list(dict.fromkeys(listaD))

        return render_template("magazzino.html", lista=myresult, listaS=listaS)

    except mysql.connector.Error as err:
        flash(f"Errore database: {err}", "error")
        return redirect(url_for('home'))


@app.route('/process', methods=['POST'])
def process():
    if request.method == 'POST':
        nome = request.form['nome']
        marca = request.form['marca']
        descrizione = request.form['descrizione']
        prezzo = request.form['prezzo']
        categoria = request.form['categoria']
        url = request.form['url']
        pezzi = request.form['pezzi']
        url2 = request.form['url2']  # Nuovo campo
        url3 = request.form['url3']  # Nuovo campo
        url4 = request.form['url4']  # Nuovo campo

        mycursor = mydb.cursor()
        sql = """
        INSERT INTO prodottipets (nome, marca, descrizione, prezzo, categoria, url, pezzi, url2, url3, url4) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        val = (nome, marca, descrizione, prezzo, categoria, url, pezzi, url2, url3, url4)

        try:
            mycursor.execute(sql, val)
            mydb.commit()
            prodotto = Prodotti(nome, marca, descrizione, prezzo, categoria, url, pezzi, 0, url2, url3, url4)
            flash("Prodotto inserito con successo!", "success")
        except mysql.connector.Error as err:
            flash(f"Errore database: {err}", "error")

    return render_template('dettagli.html', prodotto=prodotto)


@app.route('/remove', methods=['POST'])
def remove():
    if request.method == 'POST':
        prodotto_id = request.form.get('prodotto_id')

        if prodotto_id:
            mycursor = mydb.cursor()
            sql = "DELETE FROM prodottipets WHERE id = %s"
            val = (prodotto_id,)

            try:
                mycursor.execute(sql, val)
                mydb.commit()
                flash("Prodotto rimosso con successo", "success")
            except mysql.connector.Error as err:
                flash(f"Errore database: {err}", "error")

    return redirect(url_for('magazzino'))


@app.route('/edit/<int:prodotto_id>', methods=['GET', 'POST'])
def edit(prodotto_id):
    mycursor = mydb.cursor()

    if request.method == 'POST':
        nome = request.form['nome']
        marca = request.form['marca']
        descrizione = request.form['descrizione']
        prezzo = request.form['prezzo']
        categoria = request.form['categoria']
        url = request.form['url']
        url2 = request.form['url2']
        url3 = request.form['url3']
        url4 = request.form['url4']
        pezzi = request.form['pezzi']

        sql = """
            UPDATE prodottipets
            SET nome = %s, marca = %s, descrizione = %s, prezzo = %s, categoria = %s, url = %s, url2 = %s, url3 = %s, url4 = %s, pezzi = %s
            WHERE id = %s
        """
        val = (nome, marca, descrizione, prezzo, categoria, url, url2, url3, url4, pezzi, prodotto_id)

        try:
            mycursor.execute(sql, val)
            mydb.commit()
            flash("Prodotto aggiornato con successo!", "success")
        except mysql.connector.Error as err:
            flash(f"Errore database: {err}", "error")

        return redirect(url_for('magazzino'))

    try:
        sql = "SELECT * FROM prodottipets WHERE id = %s"
        mycursor.execute(sql, (prodotto_id,))
        prodotto = mycursor.fetchone()

    except mysql.connector.Error as err:
        flash(f"Errore database: {err}", "error")
        return redirect(url_for('magazzino'))

    return render_template('edit.html', prodotto=prodotto)


@app.route('/combined_chart.png')
def plot_png():
    try:
        # Esegui la query per ottenere i prodotti
        mycursor = mydb.cursor()
        mycursor.execute("SELECT * FROM prodottipets")
        prodotti = mycursor.fetchall()

        # Verifica se ci sono prodotti
        if not prodotti:
            return jsonify({"error": "Nessun prodotto trovato"}), 404

        # Estrai le etichette e le vendite
        etichette = [row[1] for row in prodotti]  # Nome del prodotto
        vendite = [row[8] if row[8] is not None else 0 for row in prodotti]  # Numero di pezzi venduti

        # Crea la figura
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))

        # Grafico a barre
        ax1.bar(etichette, vendite, color='skyblue')
        ax1.set_title('Vendite per Prodotto (Grafico a Barre)')
        ax1.set_ylabel('Vendite')
        etichette_troncate = [etichetta if len(etichetta) <= 10 else etichetta[:10] + '...' for etichetta in etichette]
        ax1.set_xticklabels(etichette_troncate, rotation=45, ha='right', fontsize=8)

        # Grafico a torta
        ax2.pie(vendite, labels=etichette_troncate, autopct='%1.1f%%', startangle=90,
                colors=['#ff9999', '#66b3ff', '#99ff99'])
        ax2.axis('equal')
        ax2.set_title('Distribuzione Vendite (Grafico a Torta)')

        # Salva la figura come PNG
        output = io.BytesIO()
        plt.savefig(output, format='png')
        plt.close(fig)
        output.seek(0)

        return Response(output.getvalue(), mimetype='image/png')

    except Exception as e:
        logging.error(f"Errore durante la generazione del grafico: {e}")
        return jsonify({"error": str(e)}), 500


# lato utente
@app.route('/store')
def store():
    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM prodottipets")
    myresult = mycursor.fetchall()

    cart = session.get('cart', [])
    total_price = sum(float(item['totale']) for item in cart)  # Converti 'totale' in float

    return render_template('store.html', lista=myresult, cart=cart, total_price=total_price)


@app.route('/search', methods=['POST'])
def search():
    keyword = request.form['keyword']
    mycursor = mydb.cursor()
    sql = """
        SELECT * FROM prodottipets 
        WHERE nome LIKE %s OR descrizione LIKE %s OR marca LIKE %s
    """
    search_term = f"%{keyword}%"
    mycursor.execute(sql, (search_term, search_term, search_term))
    search_results = mycursor.fetchall()

    cart = session.get('cart', [])
    total_price = sum(float(item["totale"]) for item in cart)  # Converti 'totale' in float

    return render_template('store.html', lista=search_results, cart=cart, total_price=total_price)


# Rotta per aggiungere al carrello
@app.route('/buy', methods=['POST'])
def buy():
    if 'cart' not in session:
        session['cart'] = []

    prodotto_id = request.form.get('prodottiN')
    quantita = int(request.form.get('prodottiA', 0))
    immagine = request.form.get('prodottiI')

    if quantita > 0:
        mycursor = mydb.cursor()
        mycursor.execute("SELECT * FROM prodottipets WHERE id = %s", (prodotto_id,))
        prodotto = mycursor.fetchone()

        pezzi_disponibili = prodotto[7]  # Assumendo che la colonna 'pezzi' sia l'ottava
        if quantita > pezzi_disponibili:
            flash(f"Spiacenti, solo {pezzi_disponibili} pezzi disponibili.", "error")
            return redirect(url_for('store'))

        # Calcola il totale
        nome = prodotto[1]
        prezzo = prodotto[4]
        totale = prezzo * quantita

        # Aggiungi il prodotto al carrello
        cart_item = next((item for item in session['cart'] if item['id'] == prodotto_id), None)
        if cart_item:
            cart_item['quantita'] += quantita
            cart_item['totale'] += totale
        else:
            session['cart'].append({
                'id': prodotto_id,
                'nome': nome,
                'quantita': quantita,
                'prezzo': prezzo,
                'immagine': immagine,
                'totale': totale
            })

        '''
        # Aggiorna il database
        nuovi_pezzi = pezzi_disponibili - quantita
        pezzi_venduti = prodotto[8] + quantita # Assumendo che 'pezziVenduti' sia la nona colonna
        print (quantita)
        print (pezzi_venduti)

        mycursor.execute("UPDATE prodottipets SET pezzi = %s, pezziVenduti = %s WHERE id = %s",
                         (nuovi_pezzi, pezzi_venduti, prodotto_id))
        mydb.commit()
        '''
        flash(f"{quantita} {nome} aggiunto al carrello!", "success")

    session.modified = True
    return redirect(url_for('store'))


@app.route('/cart')
def cart_summary():
    cart = session.get('cart', [])
    total_price = sum(float(item["totale"]) for item in cart)
    return render_template('cart.html', cart=cart, total_price=total_price)


@app.route('/empty_cart')
def empty_cart():
    session.pop('cart', None)
    flash("Il carrello è stato svuotato.", "info")
    return redirect(url_for('store'))


@app.route('/conferma_pagamento', methods=['GET', 'POST'])
def conferma_pagamento():
    if request.method == 'POST':
        cart = session.get('cart', [])
        if not cart:
            flash("Il carrello è vuoto. Aggiungi prodotti prima di procedere al pagamento.", "error")
            return redirect(url_for('store'))

        # Qui puoi aggiungere la logica di pagamento, come l'invio dei dati a un sistema di pagamento esterno.

        # Conferma il pagamento e svuota il carrello
        session.pop('cart', None)

        flash("Pagamento completato con successo!", "success")
        return redirect(url_for('pagamento_completato'))

    return redirect(url_for('cart_summary'))


@app.route('/pagamento_completato')
def pagamento_completato():
    return render_template('pagamento_completato.html')


if __name__ == '__main__':
    app.run(debug=True)