
include:
  - .{{ salt['pillar.get']('mgr_restart_init', 'default') }}

