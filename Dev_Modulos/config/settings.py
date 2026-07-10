from pathlib import Path
import sys

'''
Config de mensagens de depuração
FALSE = Não exibe
TRUE = Exibe 
'''
DEBUG = False

'''
Mapeamento de caminhos e pastas
'''
if getattr(sys, 'frozen', False):
    BASE_PATH = Path(sys.executable).parent
else:
    BASE_PATH = Path(__file__).resolve().parent.parent
