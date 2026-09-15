"""
Initialization script for Tenor-D80.

Author: Giulio Camillo, TII QRC
Version: 1.0
Date: 2026-08-07 (YYYY/DD/MM)

This script sets up the hardware configuration, instrument connections, and quantum
device representation for the Quantum Ware Tenor-D80. Platform-specific constants are defined at
the top; shared boilerplate is delegated to :mod:`init_scripts._common`.
"""

PLATFORM_NAME = "tenorD"        # Used for the data directory and device config file name.
LOAD_CFG_FILE = False           # Set True to load hardware config from the saved JSON file.
from init_scripts.hw_configs.cfg_tenorD import HW_CONFIG_DICT

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
    Initialize Tenor-D80 and return the configured QuantumDevice.

    The clusters, instrument coordinator, and measurement controls are shared
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
        print('Loading hardware configuration form dictionary')
        quantum_device.setup_config(HW_CONFIG_DICT)
        
    # Explicitly bind instruments — required by SCQT calibration routines
    quantum_device.instr_instrument_coordinator(instrument_coordinator.name)
    quantum_device.instr_measurement_control(meas_ctrl.name)
    quantum_device.instr_nested_measurement_control(nested_meas_ctrl.name)

    # -- Qubit elements --
    rows = [1,2,3,4,5,6,7,8]
    columns = ["A","B","C","D","E","F","G","H","I","J"]
    for r in rows:
        for c in columns:
            quantum_device.add_element(BasicTransmonElement(f"q{c}{r}"))

    # -- Feedline elements --
    number_of_feedlines = 10
    for i in range(number_of_feedlines):
        quantum_device.add_element(FeedlineElement(f"f{i+1}"))
    quantum_device.add_connection(quantum_device.get_element("f1"), [quantum_device.get_element(f"q{c}{r}").ports.readout() for r in rows[0:2] for c in columns[0:4]])
    quantum_device.add_connection(quantum_device.get_element("f2"), [quantum_device.get_element(f"q{c}{r}").ports.readout() for r in rows[2:4] for c in columns[0:4]])
    quantum_device.add_connection(quantum_device.get_element("f3"), [quantum_device.get_element(f"q{c}{r}").ports.readout() for r in rows[4:6] for c in columns[0:4]])
    quantum_device.add_connection(quantum_device.get_element("f4"), [quantum_device.get_element(f"q{c}{r}").ports.readout() for r in rows[6:] for c in columns[0:4]])
    quantum_device.add_connection(quantum_device.get_element("f7"), [quantum_device.get_element(f"q{c}{r}").ports.readout() for r in rows[0:2] for c in columns[6:]])
    quantum_device.add_connection(quantum_device.get_element("f8"), [quantum_device.get_element(f"q{c}{r}").ports.readout() for r in rows[2:4] for c in columns[6:]])
    quantum_device.add_connection(quantum_device.get_element("f9"), [quantum_device.get_element(f"q{c}{r}").ports.readout() for r in rows[4:6] for c in columns[6:]])
    quantum_device.add_connection(quantum_device.get_element("f10"), [quantum_device.get_element(f"q{c}{r}").ports.readout() for r in rows[6:] for c in columns[6:]])
    quantum_device.add_connection(quantum_device.get_element("f5"), [quantum_device.get_element(f"q{c}{r}").ports.readout() for r in rows[0:4] for c in columns[4:6]])
    quantum_device.add_connection(quantum_device.get_element("f6"), [quantum_device.get_element(f"q{c}{r}").ports.readout() for r in rows[4:] for c in columns[4:6]])

    # -- Initial values for qubit parameters, these should be loaded from snapshots after calibration
    pattern = [2,1,0,1,2,1,0,1,2,1] # 0,1,2 for low, mid, and high frequency labels respectively
    pattern_current = pattern
    for r in rows:
        if r != 1:
            pattern_current = [pattern[r-1]]+pattern_current.pop()
        for i in range(len(columns)):
            if pattern_current[i] == 0:
                quantum_device.get_element(f"q{c[i]}{r}").clocks.f01(3e9)
            elif pattern_current[i] == 1:
                quantum_device.get_element(f"q{c[i]}{r}").clocks.f01(4e9)
            else:
                quantum_device.get_element(f"q{c[i]}{r}").clocks.f01(5e9)
    
    # -- edges --
    # horizontal
    for r in rows:
        for i in range(len(columns[:-1])):
            q1 = quantum_device.get_element(f"q{c[i]}{r}")
            q2 = quantum_device.get_element(f"q{c[i+1]}{r}")
            hf_q = q1
            lf_q = q2
            if q2.clocks.f01() > q1.clocks.f01():
                hf_q = q2
                lf_q = q1
            quantum_device.add_edge(SuddenNetZeroEdge(child_element_name=lf_q.name, parent_element_name=hf_q.name))
    # vertical
    for c in columns:
        for i in range(len(rows[:-1])):
            q1 = quantum_device.get_element(f"q{c}{r[i]}")
            q2 = quantum_device.get_element(f"q{c}{r[i+1]}")
            hf_q = q1
            lf_q = q2
            if q2.clocks.f01() > q1.clocks.f01():
                hf_q = q2
                lf_q = q1
            quantum_device.add_edge(SuddenNetZeroEdge(child_element_name=lf_q.name, parent_element_name=hf_q.name))

    # manual removal of non-existing connections

    # -- Instrument monitor --
    publisher = InstrumentMonitorPublisher()
    publisher.start()

    return quantum_device

############################################
# 3. Script entry point
############################################

# Extend the QuantumDevice class with the initialize function, so that it can be called as QuantumDevice.initialize() to get a fully configured QuantumDevice instance.
quantum_device = initialize()
qubits = [quantum_device.get_element(f"q{c}{r}") for r in rows for c in columns]
feedlines = [quantum_device.get_element(f"f{i+1}") for i in range(number_of_feedlines)]

def start_grace():
    # -- Calibration graph --
    graph = generate_calibration_graph(quantum_device = quantum_device)
    graph.set_all_node_states("needs calibration")

    # When used as a service, generates unique run identifiers (not for interactive use):
    new_run_id(prefix='')
    register_calibration_graph(graph)
    return graph

# Turn on TWPAs
# import pyvisa

# addresses = ['192.168.0.31', '192.168.0.37']
# freqs = [6360, 6424] #MHz
# amps = [-0.1, 0.4] #dB

# for i, ip_address in enumerate(addresses):
#     rm = pyvisa.ResourceManager()
#     sgs = rm.open_resource(f'TCPIP0::{ip_address}::inst0::INSTR')
#     print(sgs.query('*IDN?'))
#     sgs.write('OUTP OFF')
#     sgs.write(f':SOUR:FREQ {freqs[i]}MHz')
#     sgs.write(f':SOUR:POW:LEV:IMM:AMPL {amps[i]}')
#     print(f'MWSOUR::{ip_address}: freq: {sgs.query(':SOURce:FREQuency?')}amp: {sgs.query(':SOUR:POW:LEV:IMM:AMPL?')}')
#     sgs.write('OUTP ON')
#     sgs.close()

# if __name__ == "__main__":    
#     pass