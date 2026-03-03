"""
Initialization script for TII QPU156.

Author: Juan Villegas, TII QRC
Version: 1.0
Date: 2026-02-26

This script sets up the hardware configuration, instrument connections, and quantum device representation for the TII QPU156. It defines the cluster configuration, including the instruments and their connectivity, and initializes the necessary components for calibration and control of the quantum device.

"""

# Import pydantic models for hardware configuration
from init_scripts._common import (
    # pydantic models for hardware configuration
    QbloxHardwareCompilationConfig, QbloxHardwareDescription, HardwareOptions, Connectivity,
    # pydantic models for settings 
    ModulationFrequencies, MixerCorrections, SoftwareDistortionCorrection, HardwareDistortionCorrection,
    # qblox module types
    ClusterModuleDescription, QCMDescription, QRMRFDescription, QCMRFDescription
)

from pydantic import ConfigDict

CLUSTER_IP = "192.168.0.2"     # IP address of the cluster. Change this if your cluster has a different IP address.
PLATFORM_NAME = "qpu156"        # This should be the same as the name used in the base_calibration notebook and the name used for the data directory. Consider changing this to a more descriptive name if you have multiple platforms.
LOAD_CFG_FILE = False            # Set to True to load hardware configuration from file, False to use the HARDWARE_CFG_TII dict defined below

hw_description = QbloxHardwareDescription(
            instrument_type="Cluster",
            ip = CLUSTER_IP,
            ref="internal", # The reference source for the instrument.
            sequence_to_file=False, # Write sequencer programs to files for (all modules in this) instrument.
            modules={
                "6": QCMRFDescription(),
                "12": QCMRFDescription(),
                "14": QCMRFDescription(),
                "20": QRMRFDescription(),
            },
        ),

HARDWARE_CFG_TII = QbloxHardwareCompilationConfig(            # This is the hardware configuration for the TII QPU156. It defines the instruments, their types, and how they are connected. Modify this according to your actual hardware setup.
    config_type =  "quantify_scheduler.backends.qblox_backend.QbloxHardwareCompilationConfig",
    hardware_description = {"cluster0": hw_description},
    hardware_options = HardwareOptions(
        latency_corrections={
            f"q{i}:mw-q{i}.01": 4e-9 for i in range(5)
        },
        modulation_frequencies= 
            # e.g "q0:res-q0.ro": {"lo_freq": 7.26e9}, ...
            {f"q{i}:{tipo1}-q{i}.{tipo2}": 
                ModulationFrequencies(lo_freq = 7.26e9) if tipo1 == "res" and tipo2 == "ro" else ModulationFrequencies(lo_freq = 3.9e9 + i*0.2e9)
            for (tipo1, tipo2) in [("res", "ro"), ("mw", "01"), ("mw", "12")]
            for i in range(5) 
        },
        output_att={
            "cluster0.module20.complex_output_0": 36, 
            "cluster0.module14.complex_output_1": 10,
            "cluster0.module6.complex_output_0": 10,
            "cluster0.module6.complex_output_1": 10,
            "cluster0.module12.complex_output_0": 10,
            "cluster0.module12.complex_output_1": 10,
        },
        input_gain={
            "cluster0.module20.complex_input_0": 0, # Gain in dB for the return signal
        },
        mixer_corrections={
             f"q{i}:{t1}-q{i}.{t2}": MixerCorrections().model_dump() for (t1, t2) in [("res", "ro"), ("mw", "01")]
             for i in range(5)
        },
        model_config = ConfigDict(
            extra="forbid",
            # ensures exceptions are raised when passing extra argument that are not
            # part of a model when initializing.
            validate_assignment=True,
            # run validation when assigning attributes
            arbitrary_types_allowed=True,
        ),
        # Software distortions correction for flux lines (example, modify as needed)
        # distortion_corrections = {
        #     f"q{i}:fl-cl0.baseband": SoftwareDistortionCorrection(
        #         filter_func="scipy.signal.lfilter",
        #             input_var_name="x",
        #             kwargs={
        #                 "b": [0, 0.25, 0.5],
        #                 "a": [1]
        #             },
        #             clipping_values=[-2.5, 2.5]
        #         ) for i in range(5)
        # },
    ),
    connectivity = Connectivity.model_validate(
        connectivity_dict := {"graph":[
            ("cluster0.module14.complex_output_1", "q0:mw"),
            ("cluster0.module6.complex_output_1", "q1:mw"),
            ("cluster0.module6.complex_output_0", "q2:mw"),
            ("cluster0.module12.complex_output_0", "q3:mw"),
            ("cluster0.module12.complex_output_1", "q4:mw"),
            # *[["cluster0.module20.complex_output_0", f"q{i}:res"] for i in range(5)],
            ("cluster0.module20.complex_input_0", ["q0:res", "q1:res","q2:res","q3:res","q4:res"]), # Probe path
            ("cluster0.module20.complex_output_0", "f0:in"), # Feedback path
        ]}
    ),
)
HARDWARE_CFG_TII["hardware_options"].modulation_frequencies["f0:in-f0.ro"] = {"lo_freq": 7.26e9}

############################################
# 1. Imports
############################################

from init_scripts._common import (
    # stdlib
    logging, time, os, Path, reload, suppress,
    # numeric / visualization
    np, plt, nx, display, SVG,
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
set_datadir(Path.home() / "nas_shared" / "Calibration" / platform_name)
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
globals()[cluster_name] = setup_cluster(cluster_name, CLUSTER_IP)

# -- Hardware abstraction layer --
instrument_coordinator = setup_instrument_coordinator(clusters=[globals()[cluster_name]])

# -- Utility instruments --
meas_ctrl, nested_meas_ctrl = setup_utilities()

# -- Quantum device --
platform_name = PLATFORM_NAME
_hw_cfg_path = Path.home() / "nas_shared" / "device_configs" / f"{PLATFORM_NAME}_config.json"
quantum_device = setup_device(
    platform_name=platform_name,
    hw_config=HARDWARE_CFG_TII,
    hw_config_path=_hw_cfg_path if (_hw_cfg_path.exists() and load_from_file) else None,
    meas_ctrl=meas_ctrl,
    nested_meas_ctrl=nested_meas_ctrl,
    instrument_coordinator=instrument_coordinator,
)

quantum_device.instr_instrument_coordinator(instrument_coordinator.name)
quantum_device.instr_measurement_control(meas_ctrl.name)
quantum_device.instr_nested_measurement_control(nested_meas_ctrl.name)

# -- Qubit elements --
qubits, edges, feedline = helper_configure_ladder(quantum_device, num_qubits=5)

# Create a pointer like 'q#' for each qubit
for i in range(len(qubits)): globals()[f'q{i}'] = qubits[i] 

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