from sleepymongoose.server import create_app
from werkzeug.serving import run_simple
import ConfigParser
import os
import sleepymongoose


def get_config():
    """
    read configuration from file specified in env variable SLEEPYMONGOOSE_CONFIG
    falls back to config.ini
    """
    config_file = os.environ.get("SLEEPYMONGOOSE_CONFIG", os.path.join(sleepymongoose.__path__[0], "config.ini"))
    print "Config file: {0}".format(config_file)
    config = ConfigParser.ConfigParser()
    config.read(config_file)
    config_dict = dict()
    for name, value in config.items("mongodb"):
        config_dict[name] = value
    return config_dict


app = create_app(config=get_config())

if __name__ == '__main__':
    run_simple('0.0.0.0', 5000, app, use_debugger=True, use_reloader=True)
