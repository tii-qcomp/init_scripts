"""
Initialization script for TII QPU167.

Author: Giulio, TII QRC
Version: 1.0
Date: 2026-04-16 (YYYY/MM/DD)

This script sets up the hardware configuration, instrument connections, and quantum
device representation for the TII QW5Q Platinum. Platform-specific constants are defined at
the top; shared boilerplate is delegated to :mod:`init_scripts._common`.
"""

CLUSTER_IP = "192.168.0.22"     # IP address of the cluster. Change this if your cluster has a different IP address.
PLATFORM_NAME = "qw5q"        # This should be the same as the name used in the base_calibration notebook and the name used for the data directory. Consider changing this to a more descriptive name if you have multiple platforms.
LOAD_CFG_FILE = True            # Set to True to load hardware configuration from file, False to use the HARDWARE_CFG_TII dict defined below
from init_scripts.hw_configs.cfg_qw5q import HW_CONFIG_DICT

############################################
# 1. Basic imports
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
    setup_cluster, setup_device, setup_instrument_coordinator, setup_utilities, setup_logging,
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

# -- Logging setup --
setup_logging(PLATFORM_NAME)
logger = logging.getLogger(PLATFORM_NAME)

#############################
# 2 configure basic settings
#############################

# -- Data directory --
_cal_data_dir = Path(os.getenv("CAL_DATA_DIR", Path.home() / "shared" / "Calibration")) / PLATFORM_NAME
set_datadir(_cal_data_dir)  # Set quantify data directory to the platform-specific calibration directory
logger.info("Data directory set to: {}".format(get_datadir()))
print("Data directory set to: {}".format(get_datadir()))

#############################
# 3 Instantiate Instruments
#############################
cluster0 = setup_cluster("cluster0", CLUSTER_IP)
instrument_coordinator = setup_instrument_coordinator(clusters=[cluster0], add_default_generic_icc = True)
meas_ctrl, nested_meas_ctrl = setup_utilities()

# -- Quantum device --
quantum_device = setup_device(
    platform_name=PLATFORM_NAME,
    meas_ctrl=meas_ctrl,
    nested_meas_ctrl=nested_meas_ctrl,
    instrument_coordinator=instrument_coordinator,
)

# Setup Device Hardware Configuration
_hw_cfg_path = Path(os.environ.get("HDW_CNFG_DIR", Path.home() / "shared" / "device_configs")) / f"{PLATFORM_NAME}_config.json"
if LOAD_CFG_FILE and _hw_cfg_path.is_file():
    quantum_device.setup_config(_hw_cfg_path)
else:
    quantum_device.setup_config(HW_CONFIG_DICT)

# Explicitly bind instruments — required by SCQT calibration routines
quantum_device.instr_instrument_coordinator(instrument_coordinator.name)
quantum_device.instr_measurement_control(meas_ctrl.name)
quantum_device.instr_nested_measurement_control(nested_meas_ctrl.name)

# Add all the qubit elements to the quantum device
from superconducting_qubit_tools.device_under_test.transmon_element import TransmonElementPurcell
quantum_device.add_element(q0 := BasicTransmonElement("q0"))
quantum_device.add_element(q1 := BasicTransmonElement("q1"))
quantum_device.add_element(q2 := BasicTransmonElement("q2"))
quantum_device.add_element(q3 := BasicTransmonElement("q3"))
quantum_device.add_element(q4 := BasicTransmonElement("q4"))
quantum_device.add_element(q0iso := BasicTransmonElement("q0iso"))
quantum_device.add_element(q1iso := BasicTransmonElement("q1iso"))
qubits = [q0, q1, q2, q3, q4]
isolated_qubits = [q0iso,q1iso]
# Add a feedline element to the quantum device and connect it to the qubits
quantum_device.add_element(feedline := FeedlineElement("f0"))
quantum_device.add_connection(feedline, [qubit.ports.readout() for qubit in qubits])

print("\n#---------------------------------------------------")
print("# Setting up Qubit Edges....")
print("#---------------------------------------------------")
print("Note: In this case, edges between Qubits are defined assuming STAR pattern of qubits on the QPU.")
print("      Change these edges as per the QPU design.")

from superconducting_qubit_tools.device_under_test.sudden_nz_edge import SuddenNetZeroEdge

edge_q2q0 = SuddenNetZeroEdge(child_element_name="q0", parent_element_name="q2")
edge_q2q1 = SuddenNetZeroEdge(child_element_name="q1", parent_element_name="q2")
edge_q3q2 = SuddenNetZeroEdge(parent_element_name="q3", child_element_name="q2")
edge_q4q2 = SuddenNetZeroEdge(parent_element_name="q4", child_element_name="q2")
    
edges = [
    edge_q2q0,
    edge_q2q1,
    edge_q3q2,
    edge_q4q2,
]
for edge in edges:
    quantum_device.add_edge(edge)

#cluster offset 
cluster0.module2.out0_offset(0.659115552902222)
cluster0.module2.out1_offset(0.276890754699707)
cluster0.module2.out2_offset(-0.215864896774292)
cluster0.module2.out3_offset(-0.447532415390015)
cluster0.module4.out0_offset(-0.587503790855408)

# Setup DC flux offsets with the QCM
q0.hardware_options.flux_bias_line.parameter("cluster0.module2.out0_offset")
q1.hardware_options.flux_bias_line.parameter("cluster0.module2.out1_offset")
q2.hardware_options.flux_bias_line.parameter("cluster0.module2.out2_offset")
q3.hardware_options.flux_bias_line.parameter("cluster0.module2.out3_offset")
q4.hardware_options.flux_bias_line.parameter("cluster0.module4.out0_offset")



# Ensure ramping is enabled on these parameters for safety
from contextlib import suppress
from quantify_scheduler.instrument_coordinator.utility import search_settable_param

for element in quantum_device.elements():
    with suppress(AttributeError):
        parameter_name = element.hardware_options.flux_bias_line.parameter()
        instrument_name, parameter_path = parameter_name.split(".", maxsplit=1)
        instrument = Instrument.find_instrument(instrument_name)
        parameter = search_settable_param(instrument, parameter_path)
        parameter.inter_delay = 0.05  # [s]
        parameter.step = 0.05  # [V]

publisher = InstrumentMonitorPublisher()
publisher.start()