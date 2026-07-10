from core.sqlite_manager import SQLiteManager

class Repository:

    def __init__(self):
        self.db = SQLiteManager()

    def inserir_email(self, dados):
        sql = """
        INSERT INTO emails(
            message_id,
            assunto,
            remetente,
            tipo,
            data_email,
            importado_em
        )
        VALUES(?,?,?,?,?,?)
        """

        self.db.execute(sql, dados)
        