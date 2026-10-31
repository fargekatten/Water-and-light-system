"""Build one sketch in isolation; avoid combining both setup()/loop() pairs."""
import argparse
from pathlib import Path
import shutil
import subprocess
import tempfile

parser = argparse.ArgumentParser()
parser.add_argument('--cli', default='arduino-cli')
parser.add_argument('--config-file')
parser.add_argument('--sketch', choices=['watering_system', 'Arduino', 'wifi_sensor'], default='watering_system')
parser.add_argument('--fqbn', default='arduino:megaavr:uno2018')
args = parser.parse_args()
repo = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='water-light-') as temporary:
    root = Path(temporary)
    sketch = root / args.sketch
    sketch.mkdir()
    source = (repo / 'firmware/wifi_sensor/wifi_sensor.ino' if args.sketch == 'wifi_sensor'
              else repo / ('watering_system.ino' if args.sketch == 'watering_system' else 'Arduino'))
    shutil.copy2(source, sketch / (args.sketch + '.ino'))
    if args.sketch != 'Arduino':
        for name in ('sensor_config.h', 'sensor_node.h'):
            if (repo / name).exists():
                shutil.copy2(repo / name, sketch / name)
    if args.sketch == 'wifi_sensor':
        for header in (repo / 'firmware/wifi_sensor').glob('*.h'):
            shutil.copy2(header, sketch / header.name)
    command = [args.cli]
    if args.config_file:
        command += ['--config-file', args.config_file]
    subprocess.run(command + ['compile', '--fqbn', args.fqbn, '--jobs', '2',
                             '--build-path', str(root / 'build'), str(sketch)], check=True)
