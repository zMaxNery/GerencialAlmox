import importlib.util
import sys
import traceback

from config.settings import BASE_PATH


class ModuleLoader:
    @staticmethod
    def carregar_modulos():
        modules = []
        pasta_modules = BASE_PATH / "modules"

        if str(BASE_PATH) not in sys.path:
            sys.path.insert(0, str(BASE_PATH))

        if not pasta_modules.exists():
            return modules

        for pasta in sorted(pasta_modules.iterdir(), key=lambda item: item.name.lower()):
            if not pasta.is_dir() or pasta.name.startswith("_"):
                continue

            manifest = pasta / "module.py"
            if not manifest.exists():
                continue

            try:
                module_name = f"gerencial_module_{pasta.name}"
                spec = importlib.util.spec_from_file_location(module_name, manifest)
                if spec is None or spec.loader is None:
                    raise ImportError(f"Não foi possível carregar {manifest}")

                modulo = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(modulo)

                if not hasattr(modulo, "NOME") or not hasattr(modulo, "abrir"):
                    raise AttributeError(
                        f"O módulo {pasta.name} precisa declarar NOME e abrir(parent)."
                    )

                modules.append(modulo)
            except Exception:
                print(f"Erro ao carregar o módulo: {pasta.name}")
                traceback.print_exc()

        return sorted(modules, key=lambda module: getattr(module, "ORDEM", 999))
