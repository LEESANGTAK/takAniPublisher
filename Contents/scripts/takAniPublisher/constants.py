import os

NAME = 'Tak Ani Publisher'
VERSION = '1.0.0'

CONTENTS_DIR = __file__.split('scripts')[0]
USER_DOCUMENTS_DIR = os.path.expanduser('~')
APP_PREFERENCE_DIR = os.path.join(USER_DOCUMENTS_DIR, 'takAniPublisher')
DEFAULT_SETTING_FILE = os.path.join(CONTENTS_DIR, 'config', 'settings.json')
USER_SETTING_FILE = os.path.join(APP_PREFERENCE_DIR, 'settings_user.json')
