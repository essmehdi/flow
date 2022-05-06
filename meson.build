project('flow', version: '0.0.1',)

pymod = import('python')
pymod.find_installation('python3')

dependency('gtk4', version: '>= 4.6.0')
dependency('libadwaita-1')

pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
moduledir = join_paths(pkgdatadir, 'flow')

subdir('resources')
subdir('flow')
subdir('extension')
subdir('po')

configure_file(
  input: 'load.py.in',
  output: 'flow',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir')
)

import('gnome').post_install(
  glib_compile_schemas: true,
  gtk_update_icon_cache: true,
  update_desktop_database: true
)