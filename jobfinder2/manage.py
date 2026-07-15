#!/usr/bin/env python
"""
Fichier de gestion Django — patché pour Python 3.12 + Django 3.2.
Python 3.12 a supprimé 'distutils' : setuptools le réintroduit.
"""
import os
import sys


def patch_distutils():
    """
    Garantit que distutils est disponible (supprimé de Python 3.12).
    setuptools >= 65 le réintroduit via son propre shim.
    """
    try:
        import distutils  # noqa: F401 — déjà présent, rien à faire
    except ImportError:
        try:
            import setuptools  # noqa: F401 — active le shim distutils de setuptools
            import distutils   # noqa: F401 — doit maintenant fonctionner
        except ImportError:
            print(
                "\n⚠ ERREUR : 'distutils' est absent et 'setuptools' n'est pas installé.\n"
                "  Corrigez avec : pip install setuptools\n",
                file=sys.stderr,
            )
            sys.exit(1)


def main():
    patch_distutils()
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobfinder.settings')
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
