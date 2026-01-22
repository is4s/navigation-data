project('navtk-data')

DATA_DIRECTORY = meson.project_source_root()

geoid_undulation_file = 'WW15MGH.GRD'

install_data(geoid_undulation_file,
             install_tag: 'runtime',
             install_dir:  get_option('datadir') / 'navtk')
