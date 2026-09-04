"""
Script de populacao de dados ficticios - Sistema Academico (ALUNO, CURSO, TURMA, MATRICULA)
Banco de dados: PostgreSQL

Volumes gerados:
    curso     -> ate 100 registros
    turma     -> ate 100 registros
    aluno     -> 100.000 registros
    matricula -> 1.000.000 registros

Requisitos:
    pip install faker psycopg2-binary

Uso:
    python popular_dados.py
"""

import random
from datetime import date, timedelta

import psycopg2
from psycopg2.extras import execute_values
from faker import Faker

fake = Faker("pt_BR")
random.seed(42)  # reprodutibilidade (opcional)

# ------------------------------------------------------------------
# Configuracao de conexao - banco Neon (Postgres serverless)
# ------------------------------------------------------------------
DB_DSN = (
    "postgresql://neondb_owner:npg_8zk5qXAQDGsZ@"
    "ep-still-dawn-ae7zkz4a-pooler.c-2.us-east-2.aws.neon.tech/"
    "neondb?sslmode=require&channel_binding=require"
)

BATCH_SIZE = 5000

QTD_CURSOS = 30
TURMAS_POR_CURSO = 3          # 30 cursos x 3 turmas = 90 turmas (<= 100)
QTD_ALUNOS = 100_000
QTD_MATRICULAS = 1_000_000

NOMES_CURSO = [
    "Administracao", "Direito", "Engenharia Civil", "Engenharia de Software",
    "Medicina", "Enfermagem", "Pedagogia", "Psicologia", "Ciencia da Computacao",
    "Arquitetura e Urbanismo", "Ciencias Contabeis", "Fisioterapia", "Odontologia",
    "Nutricao", "Educacao Fisica", "Design Grafico", "Marketing",
    "Gestao de Recursos Humanos", "Analise e Desenvolvimento de Sistemas",
    "Redes de Computadores", "Seguranca da Informacao", "Gastronomia", "Turismo",
    "Biomedicina", "Farmacia", "Medicina Veterinaria", "Jornalismo",
    "Publicidade e Propaganda", "Logistica", "Comercio Exterior",
]
NIVEIS_ESCOLARIDADE = ["Tecnico", "Graduacao", "Pos-graduacao", "Extensao"]
TURNOS = ["Manha", "Tarde", "Noite"]
STATUS_MATRICULA = ["Ativo", "Trancado", "Concluido", "Cancelado"]
ANOS_LETIVOS = [2023, 2024, 2025, 2026]


def get_connection():
    return psycopg2.connect(DB_DSN)


def popular_cursos(cursor):
    dados = []
    for nome in NOMES_CURSO[:QTD_CURSOS]:
        dados.append((
            nome,
            random.choice([1200, 1600, 2000, 2400, 3200, 4000]),
            random.choice(NIVEIS_ESCOLARIDADE),
            round(random.uniform(250.0, 2500.0), 2),
        ))
    execute_values(
        cursor,
        """INSERT INTO curso (nome_curso, carga_horaria, nivel_escolaridade, valor_mensalidade)
           VALUES %s""",
        dados,
    )
    print(f"cursos inseridos: {len(dados)}")
    return len(dados)


def popular_turmas(cursor, qtd_cursos):
    dados = []
    for id_curso in range(1, qtd_cursos + 1):
        for _ in range(TURMAS_POR_CURSO):
            dados.append((
                id_curso,
                random.choice(ANOS_LETIVOS),
                random.choice([1, 2]),
                random.choice(TURNOS),
            ))
    execute_values(
        cursor,
        """INSERT INTO turma (id_curso, ano_letivo, semestre, turno)
           VALUES %s""",
        dados,
    )
    print(f"turmas inseridas: {len(dados)}")
    return len(dados)


def gerar_cpf_unico(cpfs_usados):
    while True:
        cpf = fake.cpf()
        if cpf not in cpfs_usados:
            cpfs_usados.add(cpf)
            return cpf


def popular_alunos(cursor, conn, qtd):
    cpfs_usados = set()
    lote = []
    total_inserido = 0

    for i in range(1, qtd + 1):
        nascimento = fake.date_of_birth(minimum_age=16, maximum_age=45)
        lote.append((
            fake.name(),
            gerar_cpf_unico(cpfs_usados),
            nascimento,
            fake.unique.email() if i % 50000 != 0 else fake.email(),  # evita custo alto de unicidade
            fake.phone_number()[:15],
        ))

        if len(lote) >= BATCH_SIZE:
            execute_values(
                cursor,
                """INSERT INTO aluno (nome_completo, cpf, data_nascimento, email, telefone)
                   VALUES %s""",
                lote,
            )
            conn.commit()
            total_inserido += len(lote)
            print(f"alunos inseridos: {total_inserido}/{qtd}")
            lote = []

    if lote:
        execute_values(
            cursor,
            """INSERT INTO aluno (nome_completo, cpf, data_nascimento, email, telefone)
               VALUES %s""",
            lote,
        )
        conn.commit()
        total_inserido += len(lote)
        print(f"alunos inseridos: {total_inserido}/{qtd}")

    return total_inserido


def data_matricula_aleatoria():
    inicio = date(2023, 1, 1)
    fim = date(2026, 12, 31)
    dias = (fim - inicio).days
    return inicio + timedelta(days=random.randint(0, dias))


def popular_matriculas(cursor, conn, qtd, qtd_alunos, qtd_turmas):
    lote = []
    total_inserido = 0

    for _ in range(1, qtd + 1):
        lote.append((
            random.randint(1, qtd_alunos),
            random.randint(1, qtd_turmas),
            data_matricula_aleatoria(),
            random.choice(STATUS_MATRICULA),
        ))

        if len(lote) >= BATCH_SIZE:
            execute_values(
                cursor,
                """INSERT INTO matricula (id_aluno, id_turma, data_matricula, status_matricula)
                   VALUES %s""",
                lote,
            )
            conn.commit()
            total_inserido += len(lote)
            if total_inserido % 100_000 == 0:
                print(f"matriculas inseridas: {total_inserido}/{qtd}")
            lote = []

    if lote:
        execute_values(
            cursor,
            """INSERT INTO matricula (id_aluno, id_turma, data_matricula, status_matricula)
               VALUES %s""",
            lote,
        )
        conn.commit()
        total_inserido += len(lote)

    print(f"matriculas inseridas: {total_inserido}/{qtd}")
    return total_inserido


def main():
    conn = get_connection()
    cursor = conn.cursor()
    conn.autocommit = False

    # desliga temporariamente a validacao de FK/triggers durante a carga em massa
    # (requer que o usuario seja superuser ou dono das tabelas)
    fk_desabilitado = False
    try:
        cursor.execute("SET session_replication_role = 'replica';")
        fk_desabilitado = True
    except psycopg2.Error:
        conn.rollback()
        print("Aviso: sem permissao para desabilitar checagem de FK, seguindo com ela ativa.")

    try:
        qtd_cursos = popular_cursos(cursor)
        conn.commit()

        qtd_turmas = popular_turmas(cursor, qtd_cursos)
        conn.commit()

        popular_alunos(cursor, conn, QTD_ALUNOS)
        popular_matriculas(cursor, conn, QTD_MATRICULAS, QTD_ALUNOS, qtd_turmas)

        print("Populacao concluida com sucesso.")
    finally:
        if fk_desabilitado:
            cursor.execute("SET session_replication_role = 'origin';")
            conn.commit()
        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()
