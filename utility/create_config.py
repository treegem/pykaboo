import os
from configparser import ConfigParser


def write_config():
    project_path = os.path.join(os.path.dirname(__file__), '..')
    config_path = os.path.join(project_path, 'config.ini')

    config = ConfigParser()

    config['globals'] = {'progname': 'Pykaboo',
                         'progversion': '0.6.0'}

    config['paths'] = {'dxf': os.path.join(project_path, 'dxf'),
                       'icons': os.path.join(project_path, 'icons'),
                       'registration': project_path}

    with open(config_path, 'w') as f:
        config.write(f)
