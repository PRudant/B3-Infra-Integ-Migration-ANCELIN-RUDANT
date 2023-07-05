from flask import Flask, render_template, request, redirect, session
from flask_mysqldb import MySQL
from flask_session import Session

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Configuration de la base de données
app.config['MYSQL_HOST'] = 'localhost'  # L'adresse de ton serveur MySQL
app.config['MYSQL_USER'] = 'root'  # Ton nom d'utilisateur MySQL
app.config['MYSQL_PASSWORD'] = ''  # Ton mot de passe MySQL
app.config['MYSQL_DB'] = 'rida'  # Le nom de ta base de données MySQL

# Initialisation de l'extension MySQL
mysql = MySQL(app)


@app.route("/")
def index():
    return render_template("index.html")

import re


@app.route("/signup", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Récupération des données du formulaire d'inscription
        username = request.form["username"]
        password = request.form["password"]
        description = request.form["description"]

        # Vérification des contraintes sur le nom d'utilisateur
        if not re.match(r"^[a-zA-Z0-9_]{4,32}$", username):
            return "Le nom d'utilisateur doit contenir entre 4 et 32 caractères alphanumériques."

        # Connexion à la base de données
        cur = mysql.connection.cursor()

        # Vérification si le nom d'utilisateur existe déjà
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cur.fetchone()

        if user:
            return "Le nom d'utilisateur est déjà utilisé."

        # Insertion du nouvel utilisateur dans la table "users"
        cur.execute("INSERT INTO users (username, password, description) VALUES (%s, %s, %s)", (username, password, description))

        # Validation de la transaction
        mysql.connection.commit()

        # Fermeture du curseur
        cur.close()

        return redirect("/login")

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # Récupération des données du formulaire de connexion
        username = request.form["username"]
        password = request.form["password"]

        # Connexion à la base de données
        cur = mysql.connection.cursor()

        # Récupération de l'utilisateur correspondant aux identifiants fournis
        cur.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
        user = cur.fetchone()

        if user:
            # Enregistrement de l'utilisateur dans la session
            session["user"] = user

            return redirect("/profile")

        # Fermeture du curseur
        cur.close()

        return "Identifiants incorrects"

    return render_template("login.html")


@app.route("/logout")
def logout():
    # Suppression de l'utilisateur de la session
    session.pop("user", None)
    return redirect("/")


@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "user" not in session:
        return redirect("/login")

    # Récupération des informations de l'utilisateur à partir de la session
    user = session["user"]

    if request.method == "POST":
        # Récupération des données du formulaire de modification du profil
        new_username = request.form["new_username"]
        password = request.form["password"]
        description = request.form["description"]

        # Connexion à la base de données
        cur = mysql.connection.cursor()

        # Vérification si le nouveau pseudo existe déjà
        cur.execute("SELECT * FROM users WHERE username = %s", (new_username,))
        existing_user = cur.fetchone()

        if existing_user:
            return "Le nouveau pseudo est déjà utilisé. Veuillez en choisir un autre."

        # Mise à jour du pseudo, mot de passe et description de l'utilisateur
        cur.execute("UPDATE users SET username = %s, password = %s, description = %s WHERE id_user = %s", (new_username, password, description, user[0]))

        # Validation de la transaction
        mysql.connection.commit()

        # Mise à jour de la variable user dans la session
        user = (user[0], new_username, password, description)
        session["user"] = user

        # Fermeture du curseur
        cur.close()

        return redirect("/profile")

    return render_template("profile.html", user=user)


@app.route("/delete", methods=["GET", "POST"])
def delete():
    if request.method == "POST":
        username = request.form["username"]

        # Connexion à la base de données
        cur = mysql.connection.cursor()

        # Vérification si l'utilisateur existe dans la table "users"
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cur.fetchone()

        if user:
            # Suppression de l'utilisateur de la table "users"
            cur.execute("DELETE FROM users WHERE username = %s", (username,))
            mysql.connection.commit()
            cur.close()
            return "Compte utilisateur supprimé avec succès."

        # Fermeture du curseur
        cur.close()

        return "Utilisateur introuvable."

    return render_template("delete.html")



@app.route("/form", methods=["GET", "POST"])
def form():
    if request.method == "POST":
        text = request.form["text"]

        # Connexion à la base de données
        cur = mysql.connection.cursor()

        # Insertion du formulaire dans la table "forms"
        cur.execute("INSERT INTO forms (data) VALUES (%s)", (text,))

        # Validation de la transaction
        mysql.connection.commit()

        # Fermeture du curseur
        cur.close()

        return "Formulaire envoyé avec succès."

    return render_template("form.html")



@app.route("/forms", methods=["GET", "POST"])
def forms():
    # Connexion à la base de données
    cur = mysql.connection.cursor()

    if request.method == "POST":
        # Récupération des données du formulaire à soumettre
        form_data = request.form["form_data"]

        # Insertion du formulaire dans la table "forms"
        cur.execute("INSERT INTO forms (data) VALUES (%s)", (form_data,))

        # Validation de la transaction
        mysql.connection.commit()

    # Récupération de tous les formulaires de la table "forms"
    cur.execute("SELECT * FROM forms")
    forms = cur.fetchall()

    # Fermeture du curseur
    cur.close()

    return render_template("forms.html", forms=forms)


@app.route("/delete_form/<form_id>", methods=["POST"])
def delete_form(form_id):
    # Connexion à la base de données
    cur = mysql.connection.cursor()

    # Suppression du formulaire avec l'ID spécifié
    cur.execute("DELETE FROM forms WHERE id_forms = %s", (form_id,))

    # Validation de la transaction
    mysql.connection.commit()

    # Fermeture du curseur
    cur.close()

    return redirect("/forms")


# CODE ADMIN

@app.route("/admin", methods=["GET", "POST"])
def admin():
    # Connexion à la base de données
    cur = mysql.connection.cursor()

    # Récupération de tous les utilisateurs de la table "users"
    cur.execute("SELECT * FROM users")
    users = cur.fetchall()

    # Fermeture du curseur
    cur.close()

    if request.method == "POST":
        # Traitement des modifications des utilisateurs

        for user in users:
            username = user[0]
            password = request.form["password_" + username]
            description = request.form["description_" + username]

            # Connexion à la base de données
            cur = mysql.connection.cursor()

            # Mise à jour du mot de passe et de la description de l'utilisateur
            cur.execute("UPDATE users SET password = %s, description = %s WHERE username = %s", (password, description, username))

            # Validation de la transaction
            mysql.connection.commit()

            # Fermeture du curseur
            cur.close()

        return "Modifications enregistrées avec succès."

    return render_template("admin.html", users=users)

@app.route("/delete_user/<username>", methods=["POST"])
def delete_user(username):
    # Connexion à la base de données
    cur = mysql.connection.cursor()

    # Suppression de l'utilisateur
    cur.execute("DELETE FROM users WHERE username = %s", (username,))

    # Validation de la transaction
    mysql.connection.commit()

    # Fermeture du curseur
    cur.close()

    # Redirection vers la page d'administration
    return redirect("/admin")

@app.route("/update_user/<user_id>", methods=["POST"])
def update_user(user_id):
    # Récupération des nouvelles données du formulaire
    new_username = request.form["new_username"]
    new_password = request.form["new_password"]
    new_description = request.form["new_description"]

    # Connexion à la base de données
    cur = mysql.connection.cursor()

    # Récupération de l'ancien pseudo de l'utilisateur
    cur.execute("SELECT username FROM users WHERE id_user = %s", (user_id,))
    old_username = cur.fetchone()[0]

    if new_username != old_username:
        # Vérification si le nouveau pseudo existe déjà
        cur.execute("SELECT * FROM users WHERE username = %s", (new_username,))
        existing_user = cur.fetchone()

        if existing_user:
            return "Le nouveau pseudo est déjà utilisé. Veuillez en choisir un autre."

    # Mise à jour du pseudo, du mot de passe et de la description de l'utilisateur
    cur.execute("UPDATE users SET username = %s, password = %s, description = %s WHERE id_user = %s", (new_username, new_password, new_description, user_id))

    # Validation de la transaction
    mysql.connection.commit()

    # Fermeture du curseur
    cur.close()

    return redirect("/admin")



if __name__ == "__main__":
    app.run()
