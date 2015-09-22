import subprocess
import click


@click.command()
def main():
    """Report a crime to the deamon"""
    subprocess.call('xdg-email \
                    --utf8 \
                    --body "Lieber Ablassdaemon,\n ich möchte folgende Meldung machen:\n\n" \
                    --subject "Nachricht an den Ablassdaemon" \
                    "ablassdaemon@mrt.kit.edu"', shell=True)
