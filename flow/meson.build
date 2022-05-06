python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', join_paths(get_option('prefix'), get_option('localedir')))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'load.py.in',
  output: 'flow',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir')
)

sources = [
    '__init__.py',
    'main.py',
]

install_data(sources, install_dir: moduledir)
subdir('ui')
subdir('utils')
subdir('core')
