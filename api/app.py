import os
from flask import Flask, render_template, request, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secretkey'  # Change en production !
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'association.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Modèles
class Membre(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prenom = db.Column(db.String(80), nullable=False)
    nom = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    role = db.Column(db.String(20), default='membre')

class Cotisation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    montant = db.Column(db.Float, nullable=False)
    date = db.Column(db.String(10), nullable=False)
    membre_id = db.Column(db.Integer, db.ForeignKey('membre.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'montant': self.montant,
            'date': self.date,
            'membre_id': self.membre_id
        }

# Initialisation de la base + admin par défaut
def initialize_database():
    with app.app_context():
        db.create_all()
        if not Membre.query.first():
            admin = Membre(prenom="Admin", nom="Admin", email="admin@asso.fr", role="admin")
            db.session.add(admin)
            db.session.commit()

initialize_database()

# Routes

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/authenticate', methods=['POST'])
def authenticate():
    membre_id = request.form.get('id')
    if not membre_id:
        return redirect(url_for('login'))
    user = Membre.query.get(membre_id)
    if user:
        session['user_id'] = user.id
        session['user_role'] = user.role
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/inscription')
def inscription():
    return render_template('inscription.html')

@app.route('/inscrire', methods=['POST'])
def inscrire():
    prenom = request.form['prenom']
    nom = request.form['nom']
    email = request.form['email']

    if Membre.query.filter_by(email=email).first():
        return "Email déjà utilisé", 400

    nouveau_membre = Membre(prenom=prenom, nom=nom, email=email, role='membre')
    db.session.add(nouveau_membre)
    db.session.commit()

    return render_template('inscription_reussie.html', membre=nouveau_membre)

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = Membre.query.get(session['user_id'])
    if session['user_role'] == 'admin':
        membres = Membre.query.filter(Membre.role != 'admin').all()
        cotisations = Cotisation.query.all()
        cotisations_dict = [c.to_dict() for c in cotisations]
        total = sum(c.montant for c in cotisations)
        return render_template('admin.html', user=user, membres=membres, cotisations=cotisations, cotisations_json=cotisations_dict, total=total)
    else:
        mes_cotisations = Cotisation.query.filter_by(membre_id=user.id).all()
        return render_template('dashboard.html', user=user, cotisations=mes_cotisations)

@app.route('/ajouter_cotisation', methods=['POST'])
def ajouter_cotisation():
    if session.get('user_role') != 'admin':
        return redirect(url_for('dashboard'))
    membre_id = request.form['membre_id']
    montant = float(request.form['montant'])
    date = request.form['date']

    membre = Membre.query.get(membre_id)
    if not membre:
        return "Erreur : Membre non trouvé", 400

    nouvelle_cotisation = Cotisation(montant=montant, date=date, membre_id=membre_id)
    db.session.add(nouvelle_cotisation)
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
