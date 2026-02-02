import sys
from unittest.mock import MagicMock

# Patch entire gluon package tree
sys.modules['gluon'] = MagicMock()
sys.modules['gluon.contrib'] = MagicMock()
sys.modules['gluon.contrib.markdown'] = MagicMock()
sys.modules['gluon.http'] = MagicMock()
sys.modules['gluon.html'] = MagicMock()
sys.modules['gluon.utils'] = MagicMock()
sys.modules['gluon.tools'] = MagicMock()
sys.modules['gluon.contrib.appconfig'] = MagicMock()
