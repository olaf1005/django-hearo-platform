import os

from infrared import install_tartar, Context

ctx_name = os.environ.get("TARTAR_CONFIG")
ctx = Context(ctx_name)

if __name__ == "__main__":
    t = install_tartar.InstallTarTar(ctx)
    t.install()
