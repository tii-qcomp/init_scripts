"""
Initialization script for TII QPU164.

Author: TII QRC
Version: 1.1
Date: 2026-03-02

This script sets up the hardware configuration, instrument connections, and quantum
device representation for the TII QPU164. Platform-specific constants are defined at
the top; shared boilerplate is delegated to :mod:`init_scripts._common`.
"""

CLUSTER_IP   = "192.168.0.20"   # IP address of the cluster.
PLATFORM_NAME = "qpu164"         # Used for the data directory and device config file name.
LOAD_CFG_FILE = True             # Set True to load hardware config from the saved JSON file.

HARDWARE_CFG_TII = {
    "config_type": "quantify_scheduler.backends.qblox_backend.QbloxHardwareCompilationConfig",
    "hardware_description": {
        "cluster0": {
            "instrument_type": "Cluster",
            "ref": "internal",
            "modules": {
                "10": {"instrument_type": "QCM_RF"},
                "12": {"instrument_type": "QCM_RF"},
                "14": {"instrument_type": "QCM_RF"},
                "18": {"instrument_type": "QRM_RF"},
            },
        },
    },
    "hardware_options": {
        "modulation_frequencies": {
            "q0:res-q0.ro": {"lo_freq": 7.029e9},
            "q1:res-q1.ro": {"lo_freq": 7.029e9},
            "q2:res-q2.ro": {"lo_freq": 7.029e9},
            "q3:res-q3.ro": {"lo_freq": 7.029e9},
            "q4:res-q4.ro": {"lo_freq": 7.029e9},
            "q0:mw-q0.01":  {"lo_freq": 4.75e9},
            "q0:mw-q0.12":  {"lo_freq": 4.75e9},
            "q1:mw-q1.01":  {"lo_freq": 5.16e9},
            "q1:mw-q1.12":  {"lo_freq": 5.16e9},
            "q2:mw-q2.01":  {"lo_freq": 5.2e9},
            "q2:mw-q2.12":  {"lo_freq": 5.2e9},
            "q3:mw-q3.01":  {"lo_freq": 5.56e9},
            "q3:mw-q3.12":  {"lo_freq": 5.56e9},
            "q4:mw-q4.01":  {"lo_freq": 5.95e9},
            "q4:mw-q4.12":  {"lo_freq": 5.95e9},
        },
    },
    "connectivity": {
        "graph": [
            ["cluster0.module10.complex_output_0", "q0:mw"],
            ["cluster0.module10.complex_output_1", "q1:mw"],
            ["cluster0.module12.complex_output_0", "q2:mw"],
            ["cluster0.module12.complex_output_1", "q3:mw"],
            ["cluster0.module14.complex_output_1", "q4:mw"],
            ["cluster0.module18.complex_output_0", "q0:res"],
            ["cluster0.module18.complex_output_0", "q1:res"],
            ["cluster0.module18.complex_output_0", "q2:res"],
            ["cluster0.module18.complex_output_0", "q3:res"],
            ["cluster0.module18.complex_output_0", "q4:res"],
            ["cluster0.module18.complex_output_0", "f0:in"],
        ]
    },
}

############################################
# 1. Imports
############################################

from init_scripts._common import (
    # stdlib
    logging, time, Path, reload, suppress,
    # numeric / visualization
    np, plt, nx, display, SVG,
    # instruments
    Instrument, Cluster, qblox,
    # quantify (quantify_core fallback handled in _common)
    pqm, get_datadir, set_datadir, load_settings_onto_instrument, InstrumentMonitor,
    quantify_core, quantify_scheduler,
    InstrumentCoordinator, ClusterComponent, GenericInstrumentCoordinatorComponent,
    search_settable_param,
    # SCQT
    scqt, cal, meas, generate_calibration_graph,
    QuantumDevice, BasicTransmonElement, TransmonElementPurcell,
    TunableCouplerTransmonElement, FeedlineElement, SuddenNetZeroEdge,
    # OrangeQS / Juice
    grace, MeasurementControl, InstrumentMonitorPublisher,
    new_run_id, register_calibration_graph,
    # helpers
    setup_cluster, setup_device, setup_instrument_coordinator, setup_utilities,
    helper_configure_ladder, helper_defaults,
)

# -- Version checks --
print(f"scqt version            : {scqt.__version__}")
print(f"grace version           : {grace.__version__}")
print(f"quantify-core version   : {quantify_core.__version__}")
print(f"quantify-scheduler ver  : {quantify_scheduler.__version__}")
print(f"qblox-instruments ver   : {qblox.__version__}")

# Benchmarking start
t0 = time.time()

############################################
# 2. Configuration
############################################

# -- Logging setup --
logger = logging.getLogger(__name__)
scqt_logger = logging.getLogger("superconducting_qubit_tools")
scqt_logger.setLevel(logging.INFO)

# -- Platform identity --
platform_name = PLATFORM_NAME

# -- Data directory --
set_datadir(Path.home() / "nas_shared" / "Calibration" / platform_name)
logger.info("Data directory set to: {}".format(get_datadir()))
print("Data directory set to: {}".format(get_datadir()))

# -- Load-from-file flag --
load_from_file = LOAD_CFG_FILE if "LOAD_CFG_FILE" in globals() else False

t1 = time.time()
logger.info(f"Finished imports and configuration in {t1 - t0:.2f} s")

############################################
# 3. Instantiation
############################################

# -- Physical instruments --
cluster_name = "cluster0"
globals()[cluster_name] = setup_cluster(cluster_name, CLUSTER_IP)

# -- Hardware abstraction layer --
instrument_coordinator = setup_instrument_coordinator(clusters=[globals()[cluster_name]])

# -- Utility instruments --
meas_ctrl, nested_meas_ctrl = setup_utilities()

# -- Quantum device --
_hw_cfg_path = Path.home() / "nas_shared" / "device_configs" / f"{PLATFORM_NAME}_config.json"
quantum_device = setup_device(
    platform_name=platform_name,
    hw_config=HARDWARE_CFG_TII,
    hw_config_path=_hw_cfg_path if (_hw_cfg_path.exists() and load_from_file) else None,
    meas_ctrl=meas_ctrl,
    nested_meas_ctrl=nested_meas_ctrl,
    instrument_coordinator=instrument_coordinator,
)

# Save the hardware config to file if it doesn't exist or if loading from file is disabled
quantum_device.hardware_config.write_to_json_file(_hw_cfg_path)

# -- Qubit elements --
qubits, edges, feedline = helper_configure_ladder(quantum_device, num_qubits=5)

# Create a pointer like 'q#' for each qubit
for i in range(len(qubits)):
    globals()[f"q{i}"] = qubits[i]

helper_defaults(
    quantum_device,
    clocks=[3.742469738e9, 3.926832821e9, 3.821841118e9, 4.0e9, 4.0e9],
    readouts=[7.077309980e9, 7.166987526e9, 7.267621966e9, 7.382074503e9, 7.493387529e9],
)

# -- Calibration graph --
graph = generate_calibration_graph(quantum_device)
graph.set_all_node_states("needs calibration")

# When a service generates unique run identifiers (not for interactive use):
# new_run_id()
# register_calibration_graph(graph)

# -- Instrument monitor --
publisher = InstrumentMonitorPublisher()
publisher.start()
