"""
Initialization script for TII QPU165.

Author: Juan Villegas, TII QRC
Version: 1.0
Date: 2026-04-03

This script sets up the hardware configuration, instrument connections, and quantum
device representation for the TII QPU165. Platform-specific constants are defined at
the top; shared boilerplate is delegated to :mod:`init_scripts._common`.
"""

CLUSTER_IP    = "192.168.0.20"  # IP address of the cluster.
PLATFORM_NAME = "qpu165"        # Used for the data directory and device config file name.
LOAD_CFG_FILE = True           # Set True to load hardware config from the saved JSON file.
from init_scripts.hw_configs.cfg_qpu165 import HW_CONFIG_DICT

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

############################################
# 2. Initialization function
############################################

def initialize(
    cluster_ip: str = CLUSTER_IP,
    platform_name: str = PLATFORM_NAME,
    load_cfg_file: bool = LOAD_CFG_FILE,
) -> QuantumDevice:
    """
    Initialize QPU165 and return the configured QuantumDevice.

    Sets up the cluster, instrument coordinator, measurement controls, and
    quantum device, then populates it with a 5-qubit ladder topology and
    default clock frequencies.  Side effects:
    - Connects to the physical cluster at *cluster_ip*.
    - Sets the quantify data directory.
    - Starts the InstrumentMonitorPublisher.

    Args:
        cluster_ip:    IP address of the Qblox cluster (default: ``CLUSTER_IP``).
        platform_name: Name used for the data directory and device
                       config file (default: ``PLATFORM_NAME``).
        load_cfg_file: When ``True`` the hardware config is loaded from the
                       JSON file in ``$HDW_CNFG_DIR`` if it exists
                       (default: ``LOAD_CFG_FILE``).

    Returns:
        The fully configured :class:`QuantumDevice`.  Qubit elements are
        accessible via ``quantum_device.get_element("q0")`` etc.
    """
    # -- Version checks --
    print(f"scqt version            : {scqt.__version__}")
    print(f"grace version           : {grace.__version__}")
    print(f"quantify version        : {quantify.__version__}")
    print(f"quantify-scheduler ver  : {quantify_scheduler.__version__}")
    print(f"qblox-instruments ver   : {qblox.__version__}")

    # Benchmarking start
    t0 = time.time()

    # -- Logging setup --
    logger = logging.getLogger(__name__)
    scqt_logger = logging.getLogger("superconducting_qubit_tools")
    scqt_logger.setLevel(logging.INFO)

    # -- Data directory --
    _cal_data_dir = Path(os.getenv("CAL_DATA_DIR", Path.home() / "shared" / "Calibration")) / platform_name
    set_datadir(_cal_data_dir)  # Set quantify data directory to the platform-specific calibration directory
    logger.info("Data directory set to: {}".format(get_datadir()))
    print("Data directory set to: {}".format(get_datadir()))

    t1 = time.time()
    logger.info(f"Finished imports and configuration in {t1 - t0:.2f} s")

    # -- Physical instruments --
    cluster_name = "cluster0"
    cluster0 = setup_cluster(cluster_name, cluster_ip)

    # -- Hardware abstraction layer --
    instrument_coordinator = setup_instrument_coordinator(clusters=[cluster0])

    # -- Utility instruments --
    meas_ctrl, nested_meas_ctrl = setup_utilities()

    # -- Quantum device --

    # If load_cfg_file is True, the hardware config loads from the hardware config file in $HDW_CNFG_DIR
    _hw_cfg_path = Path(os.environ.get("HDW_CNFG_DIR", Path.home() / "shared" / "device_configs")) / f"{platform_name}_config.json"
    quantum_device = setup_device(
        platform_name=platform_name,
        hw_config=HW_CONFIG_DICT,
        hw_config_path=_hw_cfg_path if (_hw_cfg_path.exists() and load_cfg_file) else None,
        meas_ctrl=meas_ctrl,
        nested_meas_ctrl=nested_meas_ctrl,
        instrument_coordinator=instrument_coordinator,
    )

    # Explicitly bind instruments — required by SCQT calibration routines
    quantum_device.instr_instrument_coordinator(instrument_coordinator.name)
    quantum_device.instr_measurement_control(meas_ctrl.name)
    quantum_device.instr_nested_measurement_control(nested_meas_ctrl.name)

    # -- Qubit elements --
    helper_configure_ladder(quantum_device, num_qubits=5)

    # -- Initial values for qubit parameters, these should be loaded from snapshots after calibration
    helper_defaults(
        quantum_device,
        clocks=[3.742469738e9, 3.926832821e9, 3.821841118e9, 4.074357e9, 4.328310e9],
        readouts=[7.077309980e9, 7.166987526e9, 7.267621966e9, 7.384566e9, 7.492298e9],
    )

    # -- Calibration graph --
    # graph = generate_calibration_graph(quantum_device)
    # graph.set_all_node_states("needs calibration")

    # When used as a service, generates unique run identifiers (not for interactive use):
    # new_run_id()
    # register_calibration_graph(graph)

    # -- Instrument monitor --
    publisher = InstrumentMonitorPublisher()
    publisher.start()

    return quantum_device


############################################
# 3. Script entry point
############################################

if __name__ == "__main__":
    quantum_device = initialize()
    q0, q1, q2, q3, q4 = [quantum_device.get_element(f"q{i}") for i in range(5)]
    f0 = quantum_device.get_element("f0")
    qubits = [q0, q1, q2, q3, q4]
