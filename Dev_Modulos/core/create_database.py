from core.sqlite_manager import SQLiteManager

def create_database():
    db = SQLiteManager()

    db.execute("""
    CREATE TABLE IF NOT EXISTS emails(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        message_id TEXT UNIQUE,
        assunto TEXT,
        remetente TEXT,
        tipo TEXT,
        data_email TEXT,
        importado_em TEXT
    );
    """)

    db.execute("""
    CREATE TABLE IF NOT EXISTS requisicoes(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email_id INTEGER,
        numero TEXT,
        tipo TEXT,
        status TEXT,
        criado_em TEXT,
        FOREIGN KEY(email_id)
            REFERENCES emails(id)
    );
    """)

    db.execute("""
    CREATE TABLE IF NOT EXISTS itens(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        requisicao_id INTEGER,
        material TEXT,
        descricao TEXT,
        dimensao TEXT,
        quantidade REAL,
        peso REAL,
        rastreabilidade TEXT,
        maquina TEXT,
        localizacao TEXT,
        setor TEXT,
        FOREIGN KEY(requisicao_id)
            REFERENCES requisicoes(id)
    );
    """)

    db.execute("""
    CREATE TABLE IF NOT EXISTS historico(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        requisicao_id INTEGER,
        status TEXT,
        usuario TEXT,
        data TEXT,
        observacao TEXT,
        FOREIGN KEY(requisicao_id)
            REFERENCES requisicoes(id)
    );
    """)

    db.close()
