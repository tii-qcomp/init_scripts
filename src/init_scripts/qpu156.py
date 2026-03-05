"""
Initialization script for TII QPU156.

Author: Juan Villegas, TII QRC
Version: 1.1
Date: 2026-04-03

This script sets up the hardware configuration, instrument connections, and quantum
device representation for the TII QPU156. Platform-specific constants are defined at
the top; shared boilerplate is delegated to :mod:`init_scripts._common`.
"""

CLUSTER_IP = "192.168.0.2"     # IP address of the cluster. Change this if your cluster has a different IP address.
PLATFORM_NAME = "qpu156"        # This should be the same as the name used in the base_calibration notebook and the name used for the data directory. Consider changing this to a more descriptive name if you have multiple platforms.
LOAD_CFG_FILE = False            # Set to True to load hardware configuration from file, False to use the HARDWARE_CFG_TII dict defined below
from init_scripts.hw_configs import HW_CFG_QPU156 as HW_CONFIG_DICT


############################################
# 1. Imports
############################################

from init_scripts._common import (
    # stdlib
    logging, time, os, Path,
    # numeric / visualization
    np, plt, 
    # instruments
    Instrument, Cluster, qblox,
    # quantify (quantify_core fallback handled in _common)
    get_datadir, set_datadir, load_settings_onto_instrument,
    quantify, quantify_scheduler,
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
print(f"quantify version        : {quantify.__version__}")
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
_cal_data_dir = Path(os.getenv("CAL_DATA_DIR", Path.home() / "shared" / "Calibration")) / platform_name
set_datadir(_cal_data_dir)
logger.info("Data directory set to: {}".format(get_datadir()))
print("Data directory set to: {}".format(get_datadir()))

# -- Load-from-file flag --
load_from_file = LOAD_CFG_FILE if 'LOAD_CFG_FILE' in globals() else False

# -- Hardware configuration --
t1 = time.time()
logger.info(f"Finished imports and configuration in {t1 - t0:.2f} s")

############################################
# 3. Instantiation
############################################

# -- Physical instruments --
cluster_name = "cluster0"
cluster0 = setup_cluster(cluster_name, CLUSTER_IP)

# -- Hardware abstraction layer --
instrument_coordinator = setup_instrument_coordinator(clusters=[cluster0])
ic_cluster0 = instrument_coordinator.get_component(f"ic_{cluster0.name}")  # Direct access to cluster0's ClusterComponent

# -- Utility instruments --
meas_ctrl, nested_meas_ctrl = setup_utilities()

# -- Quantum device --
_hw_cfg_path = Path(os.environ.get("HDW_CNFG_DIR", Path.home() / "shared" / "device_configs")) / f"{platform_name}_config.json"
quantum_device = setup_device(
    platform_name=platform_name,
    hw_config=HW_CONFIG_DICT,
    hw_config_path=_hw_cfg_path if (_hw_cfg_path.exists() and load_from_file) else None,
    meas_ctrl=meas_ctrl,
    nested_meas_ctrl=nested_meas_ctrl,
    instrument_coordinator=instrument_coordinator,
)

# Explicitly bind instruments — required by SCQT calibration routines
quantum_device.instr_instrument_coordinator(instrument_coordinator.name)
quantum_device.instr_measurement_control(meas_ctrl.name)
quantum_device.instr_nested_measurement_control(nested_meas_ctrl.name)

# -- Qubit elements --
qubits, edges, feedline = helper_configure_ladder(quantum_device, num_qubits=5)

# Create a pointer like 'q#' for each qubit
q0, q1, q2, q3, q4 = qubits

helper_defaults(
    quantum_device,
    clocks=[3.9090e9, 4.1294e9, 4.1875e9, 4.6042e9, 4.7887e9],
    readouts=[7.078e9, 7.1878e9, 7.2941e9, 7.3841e9, 7.4987e9],
)

# -- Calibration graph --

graph = generate_calibration_graph(quantum_device)
graph.set_all_node_states("needs calibration")

# When a service is being generated this can be used to generate unique identifiers for it
# (Not for user interaction with the platform)
# new_run_id()
# register_calibration_graph(graph)

# -- Instrument monitor --

publisher = InstrumentMonitorPublisher()
publisher.start()