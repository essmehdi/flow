pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
gnome = import('gnome')

gnome.compile_resources(
    'flow',
    'com.github.essmehdi.flow.gresource.xml',
    gresource_bundle: true,
    install: true,
    install_dir: pkgdatadir,
)

subdir('icons')

install_data('com.github.essmehdi.flow.gschema.xml',
    install_dir: join_paths(get_option('datadir'), 'glib-2.0/schemas')
)

install_data(
  'com.github.essmehdi.flow.desktop',
  install_dir: join_paths(get_option('datadir'), 'applications')
)

compile_schemas = find_program('glib-compile-schemas', required: false)
if compile_schemas.found()
    test('Validate schema file', compile_schemas,
        args: ['--strict', '--dry-run', meson.current_source_dir()]
    )
endif