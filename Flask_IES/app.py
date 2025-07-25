from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
import unicodedata
import matplotlib
matplotlib.use('Agg')  
import matplotlib.pyplot as plt
import pandas as pd
import os
from collections import Counter
import numpy as np

def normalize(text):
    if not text:
        return ''
    return unicodedata.normalize('NFKD', str(text)).encode('ASCII', 'ignore').decode('ASCII').lower().strip()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///diplomas.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'supersecretkey'
db = SQLAlchemy(app)

# MODELOS
class IES(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sigla = db.Column(db.String(50))
    nome = db.Column(db.String(200))
    tipo_data_adesao = db.Column(db.String(200))
    categoria_administrativa = db.Column(db.String(100))
    regiao = db.Column(db.String(50))
    uf = db.Column(db.String(10))

class Processo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pais_ies_estrangeira = db.Column(db.String(100))
    no_ies_estrangeira = db.Column(db.String(200))
    ds_nome_curso_estrangeiro = db.Column(db.String(200))
    sg_ies = db.Column(db.String(50))
    no_ies = db.Column(db.String(200))
    etapa = db.Column(db.String(100))
    situacao_processo = db.Column(db.String(150))
    ds_curso = db.Column(db.String(200))
    no_solicitacao = db.Column(db.String(50))
    tp_solicitacao = db.Column(db.String(150))
    dt_ultima_mov = db.Column(db.String(50))

ADMIN_USER = 'admin'
ADMIN_PASS = 'admin'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/resultado')
def resultado():
    ies_nome = request.args.get('ies', '').strip()
    ies_nome_norm = normalize(ies_nome)
    processos = Processo.query.all()

    processos_estrangeira = [p for p in processos if normalize(p.no_ies_estrangeira) == ies_nome_norm]
    processos_brasil = [p for p in processos if normalize(p.no_ies) == ies_nome_norm]
    todos_processos = [p for p in processos if normalize(p.no_ies_estrangeira) == ies_nome_norm or normalize(p.no_ies) == ies_nome_norm]

    if processos_estrangeira:
        tipo = "estrangeira"
        processos_graficos = processos_estrangeira
        texto_apostila = "Teve diploma apostilado"
    elif processos_brasil:
        tipo = "brasil"
        processos_graficos = processos_brasil
        texto_apostila = f"{ies_nome}"
    else:
        tipo = None
        processos_graficos = []
        texto_apostila = ""

    if processos_graficos:
        df = pd.DataFrame([{
            'ano': p.dt_ultima_mov[-4:] if p.dt_ultima_mov and len(p.dt_ultima_mov) >= 4 else None,
            'mes': p.dt_ultima_mov[3:5] if p.dt_ultima_mov and len(p.dt_ultima_mov) >= 5 else None,
            'curso': p.ds_curso,
            'situacao': p.situacao_processo
        } for p in processos_graficos])

        df = df.dropna(subset=['ano', 'mes', 'curso', 'situacao'])
        df['curso'] = df['curso'].str.strip().str.title()
        df['situacao'] = df['situacao'].str.strip()
        df['ano'] = df['ano'].astype(str)
        df['mes'] = df['mes'].astype(str).str.zfill(2)

        os.makedirs('static/graficos', exist_ok=True)

        # Gráfico 1: Barras Horizontais - Processos por Ano
        plt.figure(figsize=(6, 4))
        df_ano = df['ano'].value_counts().sort_index()
        plt.barh(df_ano.index, df_ano.values, color='#6c0ba9')
        plt.title('Processos por Ano')
        plt.xlabel('Quantidade')
        plt.ylabel('Ano')
        plt.tight_layout()
        grafico_ano = f'static/graficos/{ies_nome_norm}_ano.png'
        plt.savefig(grafico_ano)
        plt.close()

        # Gráfico 2: Linha - Evolução dos Processos por Mês
        df_temp = df.groupby(['ano', 'mes']).size().reset_index(name='quantidade')
        df_temp['data'] = df_temp['ano'] + '-' + df_temp['mes']
        df_temp = df_temp.sort_values('data')

        plt.figure(figsize=(8, 4))
        plt.plot(df_temp['data'], df_temp['quantidade'], marker='o', color='#0077b6')
        plt.title('Evolução dos Processos por Mês')
        plt.xlabel('Ano-Mês')
        plt.ylabel('Quantidade')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        grafico_media_mes = f'static/graficos/{ies_nome_norm}_media_mes.png'
        plt.savefig(grafico_media_mes)
        plt.close()

        # Gráfico 3: Pizza - Cursos mais comuns com % e total
        from matplotlib import cm

        plt.figure(figsize=(6, 6))
        top_cursos = df['curso'].value_counts().head(6)

        def autopct_format(pct, allvals):
            total = int(round(pct/100.*np.sum(allvals)))
            return f'{pct:.1f}%\n({total})'

        plt.pie(
            top_cursos.values,
            labels=top_cursos.index,
            autopct=lambda pct: autopct_format(pct, top_cursos.values),
            startangle=140,
            colors=cm.Paired.colors,
            textprops={'fontsize': 10}
        )
        plt.title('Distribuição dos Cursos (Top 6)')
        plt.tight_layout()
        grafico_curso = f'static/graficos/{ies_nome_norm}_curso.png'
        plt.savefig(grafico_curso)
        plt.close()

        # Contagem dos processos finalizados
        num_finalizados = (df['situacao'] == 'Processo Finalizado e apostilado').sum()
    else:
        grafico_ano = grafico_media_mes = grafico_curso = None
        num_finalizados = 0

    return render_template(
        'resultado.html',
        ies_nome=ies_nome,
        processos=todos_processos,
        tipo=tipo,
        texto_apostila=texto_apostila,
        grafico_ano=grafico_ano.replace('static/', '') if grafico_ano else None,
        grafico_media_mes=grafico_media_mes.replace('static/', '') if grafico_media_mes else None,
        grafico_curso=grafico_curso.replace('static/', '') if grafico_curso else None,
        num_finalizados=num_finalizados
    )


@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        user = request.form['username']
        pwd = request.form['password']
        if user == ADMIN_USER and pwd == ADMIN_PASS:
            session['admin_logged'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Usuário ou senha incorretos.')
    return render_template('login.html')


@app.route('/admin-dashboard')
def admin_dashboard():
    if not session.get('admin_logged'):
        return redirect(url_for('admin_login'))
    ies_list = IES.query.all()
    processos = Processo.query.all()
    return render_template('admin_dashboard.html', ies_list=ies_list, processos=processos)


@app.route('/logout')
def logout():
    session.pop('admin_logged', None)
    return redirect(url_for('index'))


# CRUD IES
@app.route('/novo-ies', methods=['GET', 'POST'])
def novo_ies():
    if not session.get('admin_logged'):
        return redirect(url_for('admin_login'))
    if request.method == 'POST':
        ies = IES(
            sigla=request.form['sigla'],
            nome=request.form['nome'],
            tipo_data_adesao=request.form['tipo_data_adesao'],
            categoria_administrativa=request.form['categoria_administrativa'],
            regiao=request.form['regiao'],
            uf=request.form['uf']
        )
        db.session.add(ies)
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    return render_template('novo_ies.html')


@app.route('/editar-ies/<int:id>', methods=['GET', 'POST'])
def editar_ies(id):
    if not session.get('admin_logged'):
        return redirect(url_for('admin_login'))
    ies = IES.query.get_or_404(id)
    if request.method == 'POST':
        ies.sigla = request.form['sigla']
        ies.nome = request.form['nome']
        ies.tipo_data_adesao = request.form['tipo_data_adesao']
        ies.categoria_administrativa = request.form['categoria_administrativa']
        ies.regiao = request.form['regiao']
        ies.uf = request.form['uf']
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    return render_template('editar_ies.html', ies=ies)


@app.route('/deletar-ies/<int:id>', methods=['POST'])
def deletar_ies(id):
    if not session.get('admin_logged'):
        return redirect(url_for('admin_login'))
    ies = IES.query.get_or_404(id)
    db.session.delete(ies)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))


# CRUD Processo
@app.route('/novo-processo', methods=['GET', 'POST'])
def novo_processo():
    if not session.get('admin_logged'):
        return redirect(url_for('admin_login'))
    if request.method == 'POST':
        proc = Processo(
            pais_ies_estrangeira=request.form['pais_ies_estrangeira'],
            no_ies_estrangeira=request.form['no_ies_estrangeira'],
            ds_nome_curso_estrangeiro=request.form['ds_nome_curso_estrangeiro'],
            sg_ies=request.form['sg_ies'],
            no_ies=request.form['no_ies'],
            etapa=request.form['etapa'],
            situacao_processo=request.form['situacao_processo'],
            ds_curso=request.form['ds_curso'],
            no_solicitacao=request.form['no_solicitacao'],
            tp_solicitacao=request.form['tp_solicitacao'],
            dt_ultima_mov=request.form['dt_ultima_mov']
        )
        db.session.add(proc)
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    return render_template('novo_processo.html')


@app.route('/editar-processo/<int:id>', methods=['GET', 'POST'])
def editar_processo(id):
    if not session.get('admin_logged'):
        return redirect(url_for('admin_login'))
    proc = Processo.query.get_or_404(id)
    if request.method == 'POST':
        proc.pais_ies_estrangeira = request.form['pais_ies_estrangeira']
        proc.no_ies_estrangeira = request.form['no_ies_estrangeira']
        proc.ds_nome_curso_estrangeiro = request.form['ds_nome_curso_estrangeiro']
        proc.sg_ies = request.form['sg_ies']
        proc.no_ies = request.form['no_ies']
        proc.etapa = request.form['etapa']
        proc.situacao_processo = request.form['situacao_processo']
        proc.ds_curso = request.form['ds_curso']
        proc.no_solicitacao = request.form['no_solicitacao']
        proc.tp_solicitacao = request.form['tp_solicitacao']
        proc.dt_ultima_mov = request.form['dt_ultima_mov']
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    return render_template('editar_processo.html', proc=proc)


@app.route('/deletar-processo/<int:id>', methods=['POST'])
def deletar_processo(id):
    if not session.get('admin_logged'):
        return redirect(url_for('admin_login'))
    proc = Processo.query.get_or_404(id)
    db.session.delete(proc)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)
