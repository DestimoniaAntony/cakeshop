import os,sys,traceback
os.environ.setdefault('DJANGO_SETTINGS_MODULE','cakeshop.settings')
import django
django.setup()
from django.template.loader import get_template

try:
    t = get_template('customer/login.html')
    print('TEMPLATE LOADED OK')
    try:
        # attempt to render with empty context
        print('Rendered length:', len(t.render({})))
    except Exception as e:
        print('Render error:')
        traceback.print_exc()
except Exception:
    print('Template load error:')
    traceback.print_exc()
