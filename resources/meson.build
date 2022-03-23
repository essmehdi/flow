pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
gnome = import('gnome')

gnome.compile_resources(
    'atay',
    'com.github.essmehdi.atay.gresource.xml',
    gresource_bundle: true,
    install: true,
    install_dir: pkgdatadir,
)

subdir('icons')

install_data('com.github.essmehdi.atay.gschema.xml',
    install_dir: join_paths(get_option('datadir'), 'glib-2.0/schemas')
)

install_data(
  'com.github.essmehdi.atay.desktop',
  install_dir: join_paths(get_option('datadir'), 'applications')
)

compile_schemas = find_program('glib-compile-schemas', required: false)
if compile_schemas.found()
    test('Validate schema file', compile_schemas,
        args: ['--strict', '--dry-run', meson.current_source_dir()]
    )
endif