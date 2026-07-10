from dataclasses import dataclass

@dataclass
class Email:
    message_id: str
    assunto: str
    remetente: str
    tipo: str
    data_email: str

@dataclass
class Requisicao:
    numero: str
    tipo: str
    status: str

@dataclass
class Item:
    material: str
    descricao: str
    quantidade: float
    peso: float
