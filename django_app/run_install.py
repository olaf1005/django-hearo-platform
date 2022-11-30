from infrared import Context, install_tartar
import os

context = Context(os.environ.get("TARTAR_CONFIG"))
install_tartar.InstallTarTar(context).install()
