# init_scripts

Initialization scripts for TII QPU platforms.  Each script connects to the
physical cluster, creates the shared utility instruments, and builds a fully
configured `QuantumDevice` that can be imported by measurement notebooks or
service processes.

---

## Repository layout

```
src/init_scripts/
├── _common.py          # All shared imports and helper functions
├── qpu156.py           # Init script for QPU156
├── qpu164.py           # Init script for QPU164
├── qpu165.py           # Init script for QPU165
└── hw_configs/
    ├── __init__.py     # Re-exports all HW_CONFIG_DICT aliases
    ├── cfg_qpu156.py   # Qblox hardware compilation config for QPU156
    ├── cfg_qpu164.py   # Qblox hardware compilation config for QPU164
    └── cfg_qpu165.py   # Qblox hardware compilation config for QPU165
```

---

## How to use an existing script

### Import the ready-made `QuantumDevice`

```python
from init_scripts.qpu165 import quantum_device
```

Importing the module connects to the cluster and initializes the device
automatically.  The qubit convenience aliases are also available at module level,
as well as generic imports like numpy (`np`) and scqt (`scqt`, `meas`, `cal`)

```python
from init_scripts.qpu165 import quantum_device, q0, q1, q2, q3, q4, f0
```

### Re-initialize the device (without reconnecting instruments)

The cluster, `InstrumentCoordinator`, and `MeasurementControl` instances are
created **once** when the module is first imported.  Calling `initialize()`
again only recreates the `QuantumDevice` and its element tree, reusing the
existing hardware connections:

```python
from init_scripts.qpu165 import initialize

quantum_device = initialize()                        # default settings
quantum_device = initialize(load_cfg_file=False)     # skip JSON config file
quantum_device = initialize(load_defaults=False)     # skip default frequencies
```

### Start the Grace calibration service

```python
from init_scripts.qpu165 import quantum_device, start_grace
start_grace(quantum_device)
```

---

## Environment variables

| Variable        | Default                             | Purpose                                              |
|-----------------|-------------------------------------|------------------------------------------------------|
| `CAL_DATA_DIR`  | `~/shared/Calibration/<platform>`   | Quantify data directory root                         |
| `HDW_CNFG_DIR`  | `~/shared/device_configs`           | Directory searched for `<platform>_config.json`      |

When `LOAD_CFG_FILE = True` and `<platform>_config.json` exists in
`HDW_CNFG_DIR`, the hardware config is loaded from that file.  Otherwise the
hard-coded `HW_CONFIG_DICT` in `hw_configs/cfg_<platform>.py` is used.

---

## Adding a new platform

Follow these steps to add, for example, **QPU999**.

### Step 1 — Create the hardware config file

Create `src/init_scripts/hw_configs/cfg_qpu999.py`.  Use an existing config
as a template (e.g. `cfg_qpu165.py`) and adjust:

- `drive_modules` — slot numbers of the QCM-RF modules.
- `probe_module` — slot number(s) of the QRM-RF module(s).
- `num_qubits` — number of qubits on the chip.
- `modulation_frequencies` — per-port LO and IF frequencies.
- `hardware_options` — mixer corrections, attenuation, distortion, etc.

You can use a dictionnary, or use a pydantic definition of an object of type
`QbloxHardwareCompilationConfig` and dump it to a dictionnary.

```python
# src/init_scripts/hw_configs/cfg_qpu999.py

from quantify_scheduler.backends.qblox_backend import QbloxHardwareCompilationConfig
# ... (same imports as the other cfg_ files)

drive_modules = ["10", "12"]   # adjust to your rack layout
probe_module  = ["16"]
num_qubits    = 3

HW_CONFIG_DICT = {
    'config_type': "quantify_scheduler.backends.qblox_backend.QbloxHardwareCompilationConfig",
    **QbloxHardwareCompilationConfig(
        hardware_description={ ... },
        hardware_options={ ... },
        connectivity={ ... },
    ).model_dump(mode="json"),
}
```

### Step 2 — Register the config in `hw_configs/__init__.py`

```python
# src/init_scripts/hw_configs/__init__.py
from .cfg_qpu156 import HW_CONFIG_DICT as HW_CFG_QPU156
from .cfg_qpu164 import HW_CONFIG_DICT as HW_CFG_QPU164
from .cfg_qpu165 import HW_CONFIG_DICT as HW_CFG_QPU165
from .cfg_qpu999 import HW_CONFIG_DICT as HW_CFG_QPU999  # add this line
```

### Step 3 — Create the init script

Create `src/init_scripts/qpu999.py` by copying `qpu165.py` and changing the
four platform-specific values at the very top:

```python
# src/init_scripts/qpu999.py

CLUSTER_IP    = "192.168.0.X"   # IP address of the QPU999 cluster
PLATFORM_NAME = "qpu999"
LOAD_CFG_FILE = True
from init_scripts.hw_configs.cfg_qpu999 import HW_CONFIG_DICT
```

Then update the `initialize()` body for the new topology:

```python
# -- Qubit elements --
helper_configure_ladder(quantum_device, num_qubits=3)   # match your chip

# -- Default frequencies --
if load_defaults:
    helper_defaults(
        quantum_device,
        clocks=[4.0e9, 4.1e9, 4.2e9],     # drive frequencies per qubit
        readouts=[7.0e9, 7.1e9, 7.2e9],   # readout frequencies per qubit
    )
```

Update the module-level unpacking at the bottom to match:

```python
quantum_device = initialize()
qubits = [quantum_device.get_element(f"q{i}") for i in range(3)]
q0, q1, q2 = qubits
f0 = quantum_device.get_element("f0")
```

### Step 4 — Verify

Run the script directly to confirm the hardware connects and the device is
configured correctly:

```bash
python -m init_scripts.qpu999
```

Or from a notebook:

```python
from init_scripts.qpu999 import quantum_device
print(quantum_device.elements())
```

---

## Helper reference (`_common.py`)

| Helper | Description |
|---|---|
| `setup_cluster(name, ip)` | Connect to (or reuse) a Qblox Cluster |
| `setup_instrument_coordinator(clusters)` | Create (or reuse) the `InstrumentCoordinator` |
| `setup_utilities()` | Create (or reuse) `meas_ctrl` and `nested_meas_ctrl` |
| `setup_device(platform_name, ...)` | Create (or recreate) the `QuantumDevice` |
| `QuantumDevice.setup_config(hw_config)` | Load hardware config from a dict, Pydantic model, or JSON path |
| `helper_configure_ladder(qd, num_qubits)` | Add qubits, edges, and a feedline in a 1-D ladder topology |
| `helper_defaults(qd, clocks, readouts)` | Set default drive and readout frequencies on all qubits |
