import importlib.util
from config.settings import BASE_PATH

class ModuleLoader:

    @staticmethod
    def carregar_modulos():

        modules = []

        pasta_modules = BASE_PATH / "modules"

        if not pasta_modules.exists():
            return modules

        for pasta in pasta_modules.iterdir():

            manifest = pasta / "module.py"

            if manifest.exists():
                spec = importlib.util.spec_from_file_location(pasta.name, manifest)

                modulo = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(modulo)

                modules.append(modulo)

        return modules
    