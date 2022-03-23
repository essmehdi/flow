project('atay', version: '0.0.1',)

pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
moduledir = join_paths(pkgdatadir, 'atay')

subdir('resources')
subdir('src')
subdir('extension')
subdir('po')

configure_file(
  input: 'load.py.in',
  output: 'atay',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir')
)

configure_file(
  input: 'host.py.in',
  output: 'atay-connector',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir')
)

meson.add_install_script('build-utils/postinstall.py')
