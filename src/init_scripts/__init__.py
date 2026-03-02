"""
init_scripts – per-QPU initialization scripts for TII lab platforms.

Each QPU has its own module (e.g. ``qpu156``, ``qpu164``) that defines
platform-specific constants (IP address, hardware config, default frequencies)
and runs the full setup sequence when imported.

Shared boilerplate (instrument setup, device creation, qubit topology helpers)
lives in :mod:`init_scripts._common` and is imported by every QPU module.
"""
