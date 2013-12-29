from distutils.core import setup
import py2exe
import os

# Find GTK+ installation path
__import__('gtk')
m = sys.modules['gtk']
gtk_base_path = m.__path__[0]

setup(
	name = 'ToJPEG',
	description = 'Converts images to JPEGs',
	version = '1.0',
	windows = [{
		'script': 'src/tojpeg.py',
		#'icon_resources': [(1, 'assets/tojpeg.ico')],
	}],
	options = {
		'py2exe': {
			'packages': 'encodings',
			'includes': 'cairo, pango, pangocairo, atk, gobject, gio',
		}
	},
	data_files = [
		#assets/example.glade,
		#readme.txt,
		# If using GTK+'s builtin SVG support, uncomment these
		os.path.join(gtk_base_path, '..', 'runtime', 'bin', 'gdk-pixbuf-query-loaders.exe'),
		os.path.join(gtk_base_path, '..', 'runtime', 'bin', 'libxml2-2.dll'),
	],
)
