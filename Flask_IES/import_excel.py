import pandas as pd
from app import db, IES, Processo, app

with app.app_context():
    # Importar IES
    df_ies = pd.read_excel('data/ies-aderentes.xlsx')
    for _, row in df_ies.iterrows():
        ies = IES(
            sigla=str(row['Sigla IES']) if not pd.isna(row['Sigla IES']) else '',
            nome=str(row['Nome IES']),
            tipo_data_adesao=str(row['Tipo - Data Adesão']),
            categoria_administrativa=str(row['Categoria Administrativa']),
            regiao=str(row['Região']),
            uf=str(row['UF'])
        )
        db.session.add(ies)
    db.session.commit()
    print('IES cadastradas importadas com sucesso!')

    # Importar Processos
    df_proc = pd.read_excel('data/RELATORIO_CURSOS_DEFERIMENTO_PLENO_25-06-2025.xlsx')
    for _, row in df_proc.iterrows():
        proc = Processo(
            pais_ies_estrangeira=str(row['paisIesEstrangeira']),
            no_ies_estrangeira=str(row['noIesEstrangeira']),
            ds_nome_curso_estrangeiro=str(row['dsNomeCursoEstrangeiro']),
            sg_ies=str(row['sgIes']),
            no_ies=str(row['noIes']),
            etapa=str(row['Etapa']),
            situacao_processo=str(row['Situacao Processo']),
            ds_curso=str(row['dsCurso']),
            no_solicitacao=str(row['noSolicitacao']),
            tp_solicitacao=str(row['tpSolicitacao']),
            dt_ultima_mov=str(row['dtUltimaMov'])
        )
        db.session.add(proc)
    db.session.commit()
    print('Processos importados com sucesso!')
