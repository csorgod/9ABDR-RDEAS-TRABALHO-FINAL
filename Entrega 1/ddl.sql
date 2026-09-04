-- =========================================================
-- Sistema Acadêmico - DDL (PostgreSQL)
-- =========================================================
-- Criar o banco antes (fora de uma transação/script, ex: via psql ou pgAdmin):
--   CREATE DATABASE escola ENCODING 'UTF8';
-- Depois conecte-se a ele (\c escola no psql) e rode o restante deste script.

-- 1. Criação da tabela ALUNO
CREATE TABLE aluno (
    id_aluno SERIAL PRIMARY KEY,
    nome_completo VARCHAR(100) NOT NULL,
    cpf VARCHAR(14) UNIQUE NOT NULL,
    data_nascimento DATE NOT NULL,
    email VARCHAR(100),
    telefone VARCHAR(15)
);
 
-- 2. Criação da tabela CURSO
CREATE TABLE curso (
    id_curso SERIAL PRIMARY KEY,
    nome_curso VARCHAR(100) NOT NULL,
    carga_horaria INT NOT NULL,
    nivel_escolaridade VARCHAR(50),
    valor_mensalidade DECIMAL(10,2) NOT NULL
);
 
-- 3. Criação da tabela TURMA
CREATE TABLE turma (
    id_turma SERIAL PRIMARY KEY,
    id_curso INT NOT NULL,
    ano_letivo INT NOT NULL,
    semestre INT NOT NULL,
    turno VARCHAR(20) NOT NULL,
    CONSTRAINT fk_turma_curso FOREIGN KEY (id_curso) REFERENCES curso(id_curso)
);
 
-- 4. Criação da tabela MATRICULA
CREATE TABLE matricula (
    id_matricula SERIAL PRIMARY KEY,
    id_aluno INT NOT NULL,
    id_turma INT NOT NULL,
    data_matricula DATE NOT NULL,
    status_matricula VARCHAR(20) NOT NULL,
    CONSTRAINT fk_matricula_aluno FOREIGN KEY (id_aluno) REFERENCES aluno(id_aluno),
    CONSTRAINT fk_matricula_turma FOREIGN KEY (id_turma) REFERENCES turma(id_turma)
);