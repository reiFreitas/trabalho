from flask import Flask, render_template, request, session, url_for, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from openai import OpenAI
from functools import wraps


app = Flask(__name__)

client = OpenAI(api_key = '')
app.secret_key = '123456'
codigo_funcionario = '123456'

# Singleton
class Configuracoes:
    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
            cls.__instance.db = SQLAlchemy(app)
            cls.__instance.app_context = app.app_context()
            cls.__instance.app_context.push()
        return cls.__instance

    def pega_db(self):
        return self.db

    def encerrar(self):
        self.db.session.remove()
        self.app_context.pop()

db_conectar = Configuracoes()
db = db_conectar.pega_db()

# Classes DB
class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String, unique=True)
    senha = db.Column(db.String)

    def __init__(self, nome, senha):
        self.nome = nome
        self.senha = senha

class Ecobarreira(db.Model):
    __tablename__ = "ecobarreira"

    id = db.Column ('id', db.Integer, primary_key=True, autoincrement=True)
    nome_ecob = db.Column(db.String)
    amb_aqua = db.Column (db.String)
    tipo_residuos = db.Column (db.String)
    material_ecob = db.Column (db.String)
    ancoragem_ecob = db.Column (db.String)
    dimen_ecob = db.Column (db.String)
    custo_ecob = db.Column (db.String)

    def __init__(self, nome_ecob, amb_aqua, tipo_residuos, material_ecob, ancoragem_ecob, dimen_ecob, custo_ecob):
        self.nome_ecob = nome_ecob
        self.amb_aqua = amb_aqua
        self.tipo_residuos = tipo_residuos
        self.material_ecob = material_ecob
        self.ancoragem_ecob = ancoragem_ecob
        self.dimen_ecob = dimen_ecob
        self.custo_ecob = custo_ecob

class Funcionario(db.Model):
    __tablename__ = "funcionario"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String, unique=True)
    senha = db.Column(db.String)

    def __init__(self, nome, senha):
        self.nome = nome
        self.senha = senha


# Fachada para algumas funções BD
class Fachada:
    def __init__(self, db_conectar):
        self.db = db_conectar.pega_db()

    def add(self, instance):
        self.db.session.add(instance)
        self.db.session.commit()

    def delete(self, instance):
        self.db.session.delete(instance)
        self.db.session.commit()

    def todos(self, model):
        return model.query.all()

    def filtrar_id(self, model, id):
        return model.query.get(id)
        
    def filtrar_usuario(self, model, nome, senha):
        return model.query.filter_by(nome=nome, senha=senha).first()
        
    def filtrar_repetido(self, model, nome):
        return model.query.filter_by(nome=nome).first()

db_conectar = Configuracoes()
db_fachada = Fachada(db_conectar)

# Decorator para verificar login
def login_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    return decorated_view

def funcionario_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if 'username_funcionario' not in session:
            return redirect(url_for('login_funcionario'))
        return func(*args, **kwargs)
    return decorated_view


@app.route('/area_funcionario')
@login_required
@funcionario_required
def area_funcionario():
    ecobarreira = db_fachada.todos(Ecobarreira)
    return render_template ('area_funcionario.html', page='home', ecobarreira=ecobarreira)

@app.route('/add', methods = ['POST','GET'])
@login_required
@funcionario_required
def add():
        if request.method == 'POST':
            nome_ecob = request.form['nome_ecob']
            amb_aqua = request.form ['amb_aqua']
            tipo_residuos = request.form['tipo_residuos']
            material_ecob = request.form['material_ecob']
            ancoragem_ecob = request.form['ancoragem_ecob']
            dimen_ecob = request.form['dimen_ecob']
            custo_ecob = request.form['custo_ecob']
            ecobarreira = Ecobarreira(nome_ecob, amb_aqua, tipo_residuos, material_ecob, ancoragem_ecob, dimen_ecob, custo_ecob)
            db_fachada.add(ecobarreira)
            return redirect (url_for('area_funcionario'))
        return render_template('area_funcionario.html', page = 'add')


@app.route('/edit/<int:id>', methods = ['POST','GET'])
@funcionario_required
def edit(id):
        ecobarreira = db_fachada.filtrar_id(Ecobarreira, id)
        if request.method == 'POST':
            ecobarreira.nome_ecob = request.form['nome_ecob']
            ecobarreira.amb_aqua = request.form ['amb_aqua']
            ecobarreira.tipo_residuos = request.form['tipo_residuos']
            ecobarreira.material_ecob = request.form['material_ecob']
            ecobarreira.ancoragem_ecob = request.form['ancoragem_ecob']
            ecobarreira.dimen_ecob = request.form['dimen_ecob']
            ecobarreira.custo_ecob = request.form['custo_ecob']
            db_fachada.add(ecobarreira)
            return redirect(url_for('area_funcionario'))
        return render_template('area_funcionario.html', page = 'edit', ecobarreira = ecobarreira)

@app.route('/delete/<int:id>')
@login_required
@funcionario_required
def delete(id):
    ecobarreira = db_fachada.filtrar_id(Ecobarreira, id)
    db_fachada.delete(ecobarreira)
    return redirect (url_for('area_funcionario'))

@app.route("/login_funcionario", methods=['GET','POST'])
def login_funcionario():
    if 'username' in session:
        if 'username_funcionario' not in session:
            if request.method == 'POST':
                nome = request.form['nome']
                senha = request.form['senha']
                funcionario = db_fachada.filtrar_usuario(Funcionario, nome, senha)
                if funcionario:
                    session['username_funcionario'] = funcionario.nome
                    return redirect(url_for('area_funcionario'))
                flash('Usuário ou senha incorretos')
            return render_template('area_funcionario.html', page = 'login_funcionario')
        return redirect(url_for('area_funcionario'))
    return redirect(url_for('login'))

@app.route("/cod_acesso", methods=['GET','POST'])
@login_required
def cod_acesso():
    if request.method == 'POST':
        resposta = request.form['codigo']
        if resposta == codigo_funcionario:
            session ['liberado'] = True
            return redirect('cadastro_funcionario')
        flash('Código incorreto')
    return render_template('area_funcionario.html', page = 'cod_acesso')

@app.route('/cadastro_funcionario', methods=['GET', 'POST'])
def cadastro_funcionario():
    if 'username' in session:
        if 'username_funcionario' not in session:
            if 'liberado' in session:
                if request.method == 'POST':
                    nome = request.form['nome']
                    senha = request.form['senha']
                    funcionario = db_fachada.filtrar_repetido(Funcionario, nome)
                    if funcionario:
                        flash('Funcionário já cadastrado')
                        return redirect(url_for('cadastro_funcionario'))
                    if nome and senha:
                        funcionario = Funcionario(nome,senha)
                        db_fachada.add(funcionario)
                        return redirect(url_for('login_funcionario'))
                return render_template('area_funcionario.html', page = 'cadastro_funcionario')
            return redirect(url_for('login_funcionario'))
        return redirect (url_for('area_funcionario'))
    return redirect(url_for('login'))


@app.route('/', methods = ['POST','GET'])
@login_required
def homepage():
    return render_template('homepage.html', page = 'homepage')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' not in session:
        if request.method == 'POST':
            nome = request.form['nome']
            senha = request.form['senha']
            usuario = db_fachada.filtrar_usuario(Usuario, nome, senha)
            if usuario:
                session['username'] = usuario.nome
                return redirect(url_for('homepage'))
            flash('Usuário ou senha incorretos')
        return render_template('homepage.html', page = 'login')
    return redirect(url_for('homepage'))

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if 'username' not in session:
        if request.method == 'POST':
            nome = request.form['nome']
            senha = request.form['senha']
            usuario = db_fachada.filtrar_repetido(Usuario, nome)
            if usuario:
                flash('Esse usuário já existe')
                return redirect(url_for('cadastro'))
            if nome and senha:
                usuario = Usuario(nome,senha)
                db_fachada.add(usuario)
                return redirect(url_for('login'))
        return render_template('homepage.html', page = 'cadastro')
    return redirect(url_for('homepage'))

@app.route('/logout')
def logout():
    session.pop('liberado', None)
    session.pop('username_funcionario', None)
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route("/chatgpt", methods=['POST', 'GET'])
@login_required
def chatgpt():
    if request.method == 'POST':
    	ambiente = request.form['amb_aqua']
    	residuos = request.form['tipo_residuos']
    	material = request.form['material_ecob']
    	ancoragem = request.form['ancoragem_ecob']
    	dimensao = request.form['dimen_ecob']
    	custo = request.form['custo_ecob']
    	ecobarreiras = db_fachada.todos(Ecobarreira)
    	todas_ecob = []
    	for e in ecobarreiras:
    	    inf_ecob = {
    	        'nome_ecob': e.nome_ecob,
                'amb_aqua': e.amb_aqua,
                'tipo_residuos': e.tipo_residuos,
                'material_ecob': e.material_ecob,
                'ancoragem_ecob': e.ancoragem_ecob,
                'dimen_ecob': e.dimen_ecob,
                'custo_ecob': e.custo_ecob
                }
    	    todas_ecob.append(inf_ecob)
    	resposta = perguntar(ambiente, residuos, material, ancoragem, dimensao, custo, todas_ecob)
    	return render_template('homepage.html', page = 'chatgpt', resposta = resposta)
    return render_template('homepage.html', page = 'chatgpt')

def perguntar(ambiente, residuos, material, ancoragem, dimensao, custo, todas_ecob):
    todas_ecob_str = "\n".join([f"Nome: {e['nome_ecob']}, Ambiente: {e['amb_aqua']}, Resíduos: {e['tipo_residuos']}, Material: {e['material_ecob']}, Ancoragem: {e['ancoragem_ecob']}, Dimensão: {e['dimen_ecob']}, Custo: {e['custo_ecob']}" for e in todas_ecob])
    response = client.chat.completions.create(
    model="gpt-3.5-turbo-0125",
    response_format={ "type": "text" },
    messages=[
        {"role": "system", "content": "Você trabalha para uma empresa de ecobarreiras e irá receber informações de como o cliente quer protejar sua própria ecobarreira. Sua função é analisar as informações dada pelo cliente e indicar, dentro do nosso estoque, qual das nossas ecobarreiras melhor se encaixa no que foi pedido pelo cliente. Apresente nossas ecobarreiras pelo nome e informe o porquê da escolha. Por fim, aqui estão todas nossas ecobarreiras: "+todas_ecob_str+". Observações: finja que está falando com o cliente; sua função não é tirar dúvidas, somente recomendar uma ecobarreira; caso as informações dadas pelo cliente estejam surreais, diga que ainda não há nenhuma ecobarreira no nosso estoque adequada"},
        {"role": "user", "content": "Tipo de ambiente aquático: "+ambiente+"; Tipo de resíduos: "+residuos+"; Material da ecobarreira: "+material+"; Tipo de ancoragem da ecobarreira: "+ancoragem+"; Dimensões da ecobarreira: "+dimensao+"; Custo da ecobarreira: "+custo+""}
         ]
    )
    return response.choices[0].message.content


db.create_all()

if __name__ == '__main__':
    app.run(debug=True)