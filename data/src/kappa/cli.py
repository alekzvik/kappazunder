import typer

from kappa.stac import stac_cli
from kappa.extract import extract_cli
from kappa.wfs import wfs_cli

app = typer.Typer(name='kappa', no_args_is_help=True, help="Process Kappazunder 2020 data.")

app.add_typer(extract_cli, name='extract', no_args_is_help=True)
app.add_typer(stac_cli, name='stac', no_args_is_help=True)
app.add_typer(wfs_cli, name='wfs', no_args_is_help=True)

if __name__ == "__main__":
    app()
