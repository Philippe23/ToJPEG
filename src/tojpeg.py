#!/usr/bin/env python

# Drag and Drop file converter.

import pygtk
pygtk.require('2.0')
import gtk
import gio
import sys
import magic
import urlparse
import os.path

class ToJPEG:

	def __init__(self):
		self.jpeg_quality	= 80
		self.delete_orig	= True
		self.icon_size		= gtk.ICON_SIZE_BUTTON

		self.window			= None
		self.info_label		= gtk.Label('Drag image here')
		self.info_img		= gtk.image_new_from_stock(
									gtk.STOCK_INFO,
									self.icon_size)
		self.display_img	= gtk.image_new_from_stock(
									gtk.STOCK_DND,
									gtk.ICON_SIZE_LARGE_TOOLBAR)
		self.img_pbuf		= None
		self.img_giofile	= None
		self.button			= gtk.Button('_Convert')
		self.adv_expander	= gtk.expander_new_with_mnemonic('_Advanced Options')
		self.adv_delete_orig_checkbox	= gtk.CheckButton('Move original to the _Trash after successful conversion')
		self.adv_jpeg_quality_adjust	= gtk.Adjustment(
											value = self.jpeg_quality,
											lower = 0, upper = 100,
											step_incr = 1,
											page_incr = 10)
		self.adv_jpeg_quality_slider	= gtk.HScale(self.adv_jpeg_quality_adjust)
		
		# Use our own magic data file, as we don't want to require one be pre
		# installed.
		self.magic			= magic.Magic(
									mime=True, 
									magic_file=os.path.join('.', 'share', 'misc', 'magic') )

		self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
		self.window.set_title('Convert to JPEG')
		self.window.set_border_width(10)
		self.window.set_position(gtk.WIN_POS_CENTER)

		# Figure out window size
		def_width	= 450
		def_height	= 550
		max_scale	= 0.9
		def_ratio	= float(def_width) / def_height
		sc_width	= gtk.gdk.screen_width()
		sc_height	= gtk.gdk.screen_height()
		max_width	= int(sc_width * max_scale)
		max_height	= int(sc_height * max_scale)
		if def_width > def_height:
			if max_width < def_width:
				def_width	= int(max_width)
				def_height	= int(def_width * def_ratio)
		else:
			if max_height < def_height:
				def_height	= int(max_height)
				def_width	= int(def_height / def_ratio)

		self.window.set_default_size(def_width, def_height)

		hbox = gtk.HBox(spacing=3)
		hbox.set_border_width(3)
		hbox.pack_start(
			gtk.image_new_from_stock(gtk.STOCK_EXECUTE, gtk.ICON_SIZE_BUTTON),
			expand=False, fill=False)
		label = gtk.Label('_Convert')
		label.set_use_underline(True)
		label.set_mnemonic_widget(self.button)
		hbox.pack_start(label, expand=False, fill=True)
		self.button.remove( self.button.get_child() )
		self.button.add(hbox)

		self.window.connect('destroy', lambda w: gtk.main_quit())
		self.window.connect_after('realize', self.on_realize)
		self.adv_jpeg_quality_adjust.connect_after(
				'value-changed',
				self.on_jpeg_quality_changed)
		self.adv_delete_orig_checkbox.connect_after(
				'toggled',
				self.on_delete_orig_toggled)
		self.button.connect('clicked', self.on_convert_clicked)

		# Drag-and-Drop
		self.window.drag_dest_set(
			gtk.DEST_DEFAULT_DROP | gtk.DEST_DEFAULT_HIGHLIGHT,
			[('text/uri-list', 0, 0)],
			gtk.gdk.ACTION_COPY)
		self.window.connect('drag_drop', self.on_drop)
		self.window.connect('drag_data_received', self.on_drop_recv_data)

		self.adv_jpeg_quality_slider.set_digits(0)
		self.adv_jpeg_quality_slider.set_value_pos(gtk.POS_RIGHT)
		self.adv_jpeg_quality_slider.add_mark(0, gtk.POS_BOTTOM, 'lower quality')
		self.adv_jpeg_quality_slider.add_mark(0, gtk.POS_TOP, 'smaller file')
		self.adv_jpeg_quality_slider.add_mark(100, gtk.POS_BOTTOM, 'highest quality')
		self.adv_jpeg_quality_slider.add_mark(100, gtk.POS_TOP, 'larger file')
		
		self.info_label.set_single_line_mode(False)
		self.adv_expander.set_expanded(False)
		self.button.set_sensitive(False)

		# Layout
		main_vbox	= gtk.VBox(spacing=3)
		
		info_hbox	= gtk.HBox(spacing=3)
		info_hbox.pack_start( gtk.Label('') ) # spacer
		info_hbox.pack_start(self.info_img, expand=False, fill=False)
		info_hbox.pack_start(self.info_label, expand=False, fill=False)
		info_hbox.pack_start( gtk.Label('') ) # spacer
		
		jpeg_quality_label	= gtk.Label('JPEG _Quality')
		jpeg_quality_label.set_use_underline(True)
		jpeg_quality_label.set_mnemonic_widget(self.adv_jpeg_quality_slider)
		jpeg_quality_hbox	= gtk.HBox(spacing=8)
		jpeg_quality_hbox.pack_start(jpeg_quality_label, expand=False, fill=False)
		jpeg_quality_hbox.pack_start(self.adv_jpeg_quality_slider, expand=True, fill=True)
		
		adv_vbox	= gtk.VBox(spacing=3)
		adv_vbox.pack_start(self.adv_delete_orig_checkbox)
		adv_vbox.pack_start(jpeg_quality_hbox)
		#adv_vbox.pack_end(gtk.HSeparator(), expand=False, fill=False)
		
		alignment	= gtk.Alignment(xscale=1.0, yscale=1.0)
		alignment.set_padding(0, 0, 20, 0)
		alignment.add(adv_vbox)

		self.adv_expander.add(alignment)
		
		bbox		= gtk.HButtonBox()
		bbox.set_layout(gtk.BUTTONBOX_END)
		bbox.pack_end(self.button, fill=False, expand=False)
		
		
		
		main_vbox.pack_start(info_hbox, expand=False)
		main_vbox.pack_start(gtk.HSeparator(), expand=False, fill=False)
		main_vbox.pack_start(self.display_img, expand=True, fill=True)
		main_vbox.pack_start(gtk.HSeparator(), expand=False, fill=False)
		main_vbox.pack_end(bbox, expand=False, fill=False)
		main_vbox.pack_end(self.adv_expander, expand=False, fill=False)
		
		
		self.window.add(main_vbox)


		self.window.show_all()

		self.unload_image()




	def on_realize(self, widget):
		#self.display_img.connect_after('size-allocate', self.on_size_allocate)
		pass
	
	def on_jpeg_quality_changed(self, adjustment):
		self.jpeg_quality = int( adjustment.get_value() )
	
	def on_delete_orig_toggled(self, toggle):
		self.delete_orig = toggle.get_active()
	
	def on_convert_clicked(self, button):
		try:
			self.save_image_as_jpeg()
		except Exception as e:
			self.show_error(str(e))

	def on_drop(self, widget, context, x, y, time):
		print 'on_drop'
		widget.drag_get_data(context, context.targets[0], time)
		return True

	def on_drop_recv_data(self, widget, context, x, y, data, info, time):
		print 'on_drop_recv_data', context.targets
		uris = data.get_uris()
		for d in uris:
			print "\t", d
		if len(uris) > 1:
			self.error_dialog('Too many files, only one at a time is supported.')
		elif len(uris) < 1:
			context.finish(False, False, time)
			return
		
		try:
			f = gio.File(uris[0])
			
			self.load_image(f)
			
			context.finish(True, False, time)
		except Exception as e:
			print 'Failed:', str(e)
			context.finish(False, False, time)

	def is_image_loaded(self):
		return self.img_pbuf is not None

	def do_load_image(self, giofile):
		if not isinstance(giofile, gio.File):
			giofile			= gio.File(giofile)

		self.img_pbuf		= gtk.gdk.pixbuf_new_from_file( giofile.get_path() )
		self.img_giofile	= giofile

		self.show_instruction('Click "Convert".')

		self.handle_resize()
	
	def load_image(self, giofile):
		if not isinstance(giofile, gio.File):
			giofile		= giofile.File(giofile)

		self.unload_image()
		is_jpeg			= self.is_file_already_jpeg(giofile)

		try:
			self.do_load_image(giofile)

			if is_jpeg:
				self.show_error(
					'{0} is already a jpeg; no need to convert.  Drag another file.',
					giofile.get_basename() )
				self.button.set_sensitive(False)
			else:
				self.button.set_sensitive(True)

		except Exception as e:
			self.show_error(str(e))

	def unload_image(self):
		self.img_pbuf		= None
		self.img_giofile	= None
		self.display_img.set_from_stock(
			gtk.STOCK_DND,
			gtk.ICON_SIZE_LARGE_TOOLBAR)
		self.show_instruction('Drag image here')

	def is_file_already_jpeg(self, giofile=None):
		if giofile is None:
			giofile = self.img_giofile
		if giofile is None:
			return False
		if not isinstance(giofile, gio.File):
			giofile = gio.File(giofile)

		
		return self.magic.from_file( giofile.get_path() ) == 'image/jpeg'

	def save_image_as_jpeg(self, output_giofile=None):
		if self.img_pbuf is None:
			return

		if output_giofile is None:
			output_giofile = self.img_giofile
			if not isinstance(output_giofile, gio.File):
				output_giofile = gio.File(output_giofile)
			# Change extension
			uri_str = output_giofile.get_uri()
			parts = urlparse.urlsplit(uri_str)
			path = parts[2]
			(base, ext) = os.path.splitext(path)
			newpath = base + '.jpg'
			parts = [p for p in parts]
			parts[2] = newpath
			newuri = urlparse.urlunsplit(parts)
			output_giofile = gio.File(newuri)

		if not isinstance(output_giofile, gio.File):
			output_giofile = gio.File(output_giofile)

		# Refuse to overwrite
		if output_giofile.query_exists():
			msg = str.format('File already exists: {0}', output_giofile.get_path())
			raise Exception(msg)

		options = { 'quality': str(self.jpeg_quality) }
		print 'SAVING:', output_giofile.get_path(), 'with options', str(options)
		self.img_pbuf.save(output_giofile.get_path(), 'jpeg', options)
	
	def error_dialog(self, format, *args):
		gtk.MessageDialog(
			self.window,
			gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
			gtk.MESSAGE_ERROR,
			gtk.BUTTONS_OK,
			format,
			*args)

	def on_size_allocate(self, widget, allocation):
		self.handle_resize()
	
	def show_instruction(self, msg, *args):
		self.info_img.set_from_stock(gtk.STOCK_INFO, self.icon_size)
		text = str.format(msg, *args)
		self.info_label.set_text(text)
		print 'INSTRUCTION:', text
	
	def show_error(self, msg, *args):
		self.info_img.set_from_stock(gtk.STOCK_DIALOG_ERROR, self.icon_size)
		text = str.format(msg, *args)
		text = 'ERROR: ' + text
		self.info_label.set_text(text)
		print text
		

	def handle_resize(self):
		if self.img_pbuf is None:
			return

		disp_rect	= self.display_img.get_allocation()
		disp_width	= disp_rect.width
		disp_height	= disp_rect.height
		pbuf_width	= self.img_pbuf.get_width()
		pbuf_height	= self.img_pbuf.get_height()

		if disp_width <= 0 or disp_height <= 0:
			return
		if pbuf_width <= 0 or pbuf_height <= 0:
			return

		pbuf_ratio	= float(pbuf_width) / pbuf_height
		img_width	= disp_width
		img_height	= disp_height
		if disp_width < disp_height:
			img_height	= img_width / pbuf_ratio
		else:
			img_width	= img_height * pbuf_ratio
		img_width	= int(img_width + 0.5)
		img_height	= int(img_height + 0.5)

		disp_pbuf = self.img_pbuf.scale_simple(
			img_width, img_height,
			gtk.gdk.INTERP_BILINEAR)

		self.display_img.set_from_pixbuf(disp_pbuf)


		



if __name__ == '__main__':
	inst = ToJPEG()

	if len(sys.argv) > 2:
		# Warn about too many arguments
		pass
	elif len(sys.argv) == 2:
		# :TODO: Need to catch errors
		f = gio.File(sys.argv[1])
		print str(f)
		inst.load_image(f)

	gtk.main()


# vim: ai:ts=4:sw=4
