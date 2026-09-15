"""
Initialization script for TUNA-5.

Author: Giulio Camillo, TII QRC
Version: 1.0
Date: 2026-19-08 (YYYY/DD/MM)

This script sets up the hardware configuration, instrument connections, and quantum
device representation for the TUNA-5. Platform-specific constants are defined at
the top; shared boilerplate is delegated to :mod:`init_scripts._common`.
"""

CLUSTER_IP    = "192.168.0.6"  # IP address of the cluster.
PLATFORM_NAME = "tuna5"        # Used for the data directory and device config file name.
LOAD_CFG_FILE = False           # Set True to load hardware config from the saved JSON file.
from init_scripts.hw_configs.cfg_tuna5 import HW_CONFIG_DICT

HW_CONFIG_DICT['hardware_description']['cluster']['ip']=CLUSTER_IP
############################################
# 1. Imports
############################################

from init_scripts._common import (
    logging, time, os, Path, # stdlib
    np, plt, # numeric / visualization
    Instrument, Cluster, qblox, # instruments
    get_datadir, set_datadir, load_settings_onto_instrument,
    # quantify and SCQT
    quantify, qblox_scheduler,
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

############################################
# 2. Utilities (created once, reused across initialize() calls)
############################################
instrument_coordinator = setup_instrument_coordinator()
meas_ctrl, nested_meas_ctrl = setup_utilities()

############################################
# 3. Initialization function
############################################

def initialize(
    platform_name: str = PLATFORM_NAME,
    load_cfg_file: bool = LOAD_CFG_FILE,
    load_defaults: bool = True,
) -> QuantumDevice:
    """
    Initialize tuna5 and return the configured QuantumDevice.

    The cluster, instrument coordinator, and measurement controls are shared
    module-level singletons created once on import.  Calling ``initialize()``
    again safely recreates only the QuantumDevice (and its element tree) while
    reusing those existing utilities.

    Args:
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
    print(f"qblox-scheduler ver     : {qblox_scheduler.__version__}")
    print(f"qblox-instruments ver   : {qblox.__version__}")

    # Benchmarking start
    t0 = time.time()

    # -- Logging setup --
    setup_logging(platform_name)
    logger = logging.getLogger(platform_name)

    # -- Data directory --
    _cal_data_dir = Path(os.getenv("CAL_DATA_DIR", Path.home() / "shared" / "Calibration")) / platform_name
    set_datadir(_cal_data_dir)  # Set quantify data directory to the platform-specific calibration directory
    logger.info("Data directory set to: {}".format(get_datadir()))
    print("Data directory set to: {}".format(get_datadir()))

    t1 = time.time()
    logger.info(f"Finished imports and configuration in {t1 - t0:.2f} s")

    # -- Quantum device --
    quantum_device = setup_device(
        platform_name=platform_name,
        meas_ctrl=meas_ctrl,
        nested_meas_ctrl=nested_meas_ctrl,
        instrument_coordinator=instrument_coordinator,
    )

    # Setup Device Hardware Configuration
    _hw_cfg_path = Path(os.environ.get("HDW_CNFG_DIR", Path.home() / "shared" / "device_configs")) / f"{platform_name}_config.json"
    if load_cfg_file and _hw_cfg_path.is_file():
        quantum_device.setup_config(_hw_cfg_path)
    else:
        print('Loading hardware configuration form dictionnary')
        quantum_device.setup_config(HW_CONFIG_DICT)
        
    # Explicitly bind instruments — required by SCQT calibration routines
    quantum_device.instr_instrument_coordinator(instrument_coordinator.name)
    quantum_device.instr_measurement_control(meas_ctrl.name)
    quantum_device.instr_nested_measurement_control(nested_meas_ctrl.name)

    # -- Qubit elements --
    # qubits
    qubits = []
    for name in ["q0","q1","q2","q3","q4"]:
        quantum_device.add_element(q := TransmonElementPurcell(name))
        qubits.append(q)

    # tunable couplers
    tunable_couplers = []
    for name in ["02","12","23","24"]:
        quantum_device.add_edge(tc := TunableCouplerTransmonElement(name="tc"+name, child_element_name="q"+name[0], parent_element_name="q"+name[1]))
        tunable_couplers.append(tc)

    # the feedline
    quantum_device.add_element(feedline := FeedlineElement("f0"))
    quantum_device.add_connection(feedline, [qubit.ports.readout() for qubit in qubits])

    # -- Initial values for qubit parameters, these should/will be overridden from snapshots after calibration
    clocks = [5.347e9,5.486e9,5.515e9,5.582e9,5.710e9]
    readouts = [7.01e9,7.21e9,7.40e9,7.60e9,7.79e9]

    for i in range(5):
        qubits[i].clock_freqs.f01(clocks[i])
        qubits[i].clock_freqs.readout(readouts[i])
    
    # -- Instrument monitor --
    publisher = InstrumentMonitorPublisher()
    publisher.start()

    return quantum_device

############################################
# 3. Script entry point
############################################

# Extend the QuantumDevice class with the initialize function, so that it can be called as QuantumDevice.initialize() to get a fully configured QuantumDevice instance.
quantum_device = initialize()
qubits = [quantum_device.get_element(f"q{i}") for i in range(5)]
q0, q1, q2, q3, q4 = qubits
tunable_couplers = [quantum_device.get_element("tc"+x) for x in ["02","12","23","24"]]
tc02, tc12, tc23, tc24 = tunable_couplers
feedlines = [quantum_device.get_element(f"f{i}") for i in range(1)]
f0 = feedlines

# flux channels
q4.hardware_options.flux_bias_line.parameter("cluster.module6.out0_offset")
q0.hardware_options.flux_bias_line.parameter("cluster.module8.out0_offset")
q1.hardware_options.flux_bias_line.parameter("cluster.module8.out1_offset")
q2.hardware_options.flux_bias_line.parameter("cluster.module8.out2_offset")
q3.hardware_options.flux_bias_line.parameter("cluster.module8.out3_offset")

tc02.hardware_options.flux_bias_line.parameter("cluster.module4.out0_offset")
tc12.hardware_options.flux_bias_line.parameter("cluster.module4.out1_offset")
tc23.hardware_options.flux_bias_line.parameter("cluster.module4.out2_offset")
tc24.hardware_options.flux_bias_line.parameter("cluster.module4.out3_offset")

def start_grace():
    # -- Calibration graph --
    graph = generate_calibration_graph(quantum_device = quantum_device)
    graph.set_all_node_states("needs calibration")

    # When used as a service, generates unique run identifiers (not for interactive use):
    new_run_id(prefix='')
    register_calibration_graph(graph)
    return graph

# Turn on TWPAs
import pyvisa

# addresses = ['192.168.0.35']
addresses = ['192.168.0.31']
# freqs = [8824]#[8468] #MHz
# amps = [-16]#[-13.8] #dB
freqs = [7000] #MHz
amps = [-13.5] #dB

for i, ip_address in enumerate(addresses):
    rm = pyvisa.ResourceManager()
    sgs = rm.open_resource(f'TCPIP0::{ip_address}::inst0::INSTR')
    print(sgs.query('*IDN?'))
    sgs.write('OUTP OFF')
    sgs.write(f':SOUR:FREQ {freqs[i]}MHz')
    sgs.write(f':SOUR:POW:LEV:IMM:AMPL {amps[i]}')
    print(f'MWSOUR::{ip_address}: freq: {sgs.query(':SOURce:FREQuency?')}amp: {sgs.query(':SOUR:POW:LEV:IMM:AMPL?')}')
    sgs.write('OUTP ON')
    sgs.close()

if __name__ == "__main__":    
    pass