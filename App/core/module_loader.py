from __future__ import annotations

import importlib
import importlib.util
import sys
import traceback
from pathlib import Path
from types import ModuleType

from config.settings import BASE_PATH


class ModuleLoader:
    PREFIXO_MODULO = "almox_modulo_"

    @staticmethod
    def _pasta_modules() -> Path:
        return BASE_PATH / "modules"

    @classmethod
    def descarregar_modulos(cls) -> None:
        """Remove da memória os módulos carregados da pasta externa modules."""
        pasta_modules = cls._pasta_modules().resolve()
        nomes_para_remover: list[str] = []

        for nome, modulo in list(sys.modules.items()):
            remover = False

            if nome.startswith(cls.PREFIXO_MODULO):
                remover = True
            if nome == "modules" or nome.startswith("modules."):
                remover = True

            arquivo = getattr(modulo, "__file__", None)
            if arquivo:
                try:
                    caminho = Path(arquivo).resolve()
                    if caminho.is_relative_to(pasta_modules):
                        remover = True
                except (OSError, ValueError):
                    pass

            if remover:
                nomes_para_remover.append(nome)

        nomes_para_remover.sort(
            key=lambda item: item.count("."),
            reverse=True,
        )

        for nome in nomes_para_remover:
            sys.modules.pop(nome, None)

        importlib.invalidate_caches()

    @classmethod
    def carregar_modulos(cls, recarregar: bool = False) -> list[ModuleType]:
        """Carrega os módulos encontrados na pasta externa ``modules``."""
        modulos: list[ModuleType] = []
        pasta_modules = cls._pasta_modules()

        if recarregar:
            cls.descarregar_modulos()

        if not pasta_modules.exists():
            return modulos

        if str(BASE_PATH) not in sys.path:
            sys.path.insert(0, str(BASE_PATH))
        importlib.invalidate_caches()

        for pasta in sorted(
            pasta_modules.iterdir(),
            key=lambda item: item.name.lower(),
        ):
            if not pasta.is_dir() or pasta.name.startswith("_"):
                continue

            manifest = pasta / "module.py"
            if not manifest.exists():
                continue

            nome_modulo = f"{cls.PREFIXO_MODULO}{pasta.name}"
            try:
                spec = importlib.util.spec_from_file_location(
                    nome_modulo,
                    manifest,
                )
                if spec is None or spec.loader is None:
                    raise ImportError(f"Não foi possível carregar {manifest}.")

                modulo = importlib.util.module_from_spec(spec)
                sys.modules[nome_modulo] = modulo
                spec.loader.exec_module(modulo)

                if not hasattr(modulo, "NOME"):
                    raise AttributeError(
                        f"O módulo '{pasta.name}' não declarou NOME."
                    )
                if not hasattr(modulo, "abrir"):
                    raise AttributeError(
                        f"O módulo '{pasta.name}' não declarou abrir(parent)."
                    )
                if not callable(modulo.abrir):
                    raise TypeError(
                        f"abrir não é uma função no módulo '{pasta.name}'."
                    )

                # O código usado nas permissões é o CODIGO declarado pelo
                # módulo ou, na ausência dele, o nome da própria pasta.
                codigo = str(
                    getattr(modulo, "CODIGO", pasta.name)
                ).strip().lower()
                if not codigo:
                    raise AttributeError(
                        f"O módulo '{pasta.name}' possui CODIGO inválido."
                    )

                modulo.CODIGO = codigo
                modulo.PASTA_MODULO = pasta
                modulos.append(modulo)

            except Exception:
                sys.modules.pop(nome_modulo, None)
                print(f"Erro ao carregar o módulo: {pasta.name}")
                traceback.print_exc()

        return sorted(
            modulos,
            key=lambda modulo: (
                getattr(modulo, "ORDEM", 999),
                str(getattr(modulo, "NOME", "")).lower(),
            ),
        )
