"""Locate native KiCad and prepare project-local, versioned library configuration."""
import os
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
APP = Path('/Applications/KiCad/KiCad.app/Contents')


def environment():
    env = dict(os.environ)
    if not APP.exists():
        config = ROOT / '.scratch/kicad-config'
        (config / '10.0').mkdir(parents=True, exist_ok=True)
        for name, header in [('sym-lib-table', 'sym_lib_table'), ('fp-lib-table', 'fp_lib_table')]:
            (config / '10.0' / name).write_text(f'({header} (version 7))\n')
        env['KICAD_CONFIG_HOME'] = str(config)
    if APP.exists():
        support = APP / 'SharedSupport'
        config = ROOT / '.scratch/kicad-config'
        (config / '10.0').mkdir(parents=True, exist_ok=True)
        for name in ('sym-lib-table', 'fp-lib-table'):
            shutil.copy2(support / 'template' / name, config / '10.0' / name)
        env.update(KICAD_CONFIG_HOME=str(config), KICAD10_SYMBOL_DIR=str(support / 'symbols'),
                   KICAD10_FOOTPRINT_DIR=str(support / 'footprints'), KICAD10_3DMODEL_DIR=str(support / '3dmodels'))
    return env


def cli():
    return os.environ.get('KICAD_CLI') or shutil.which('kicad-cli') or str(ROOT / 'tools/kicad-cli')


def python():
    return os.environ.get('KICAD_PYTHON') or str(ROOT / 'tools/kicad-python')
