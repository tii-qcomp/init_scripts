"""
Initialization script for TII QPU156.

Author: Juan Villegas, TII QRC
Version: 1.1
Date: 2026-04-03

This script sets up the hardware configuration, instrument connections, and quantum
device representation for the TII QPU156. Platform-specific constants are defined at
the top; shared boilerplate is delegated to :mod:`init_scripts._common`.
"""

# Import pydantic models for hardware configuration
from init_scripts._common import (
    # pydantic models for hardware configuration
    QbloxHardwareCompilationConfig,
    ClusterSettings, AnalogModuleSettings, RFModuleSettings, Connectivity,
    QbloxHardwareDescription, ClusterDescription, ClusterModuleDescription, QbloxHardwareOptions,
    # pydantic models for parameters 
    ModulationFrequencies, QbloxHardwareDistortionCorrection, QbloxMixerCorrections,  ComplexInputGain, InputAttenuation, OutputAttenuation ,
    # qblox module types
    QRMDescription, QCMDescription, QRMRFDescription, QCMRFDescription, QTMDescription, 
)

CLUSTER_IP = "192.168.0.2"     # IP address of the cluster. Change this if your cluster has a different IP address.
PLATFORM_NAME = "qpu156"        # This should be the same as the name used in the base_calibration notebook and the name used for the data directory. Consider changing this to a more descriptive name if you have multiple platforms.
LOAD_CFG_FILE = False            # Set to True to load hardware configuration from file, False to use the HARDWARE_CFG_TII dict defined below

HARDWARE_CFG_TII = QbloxHardwareCompilationConfig(            # This is the hardware configuration for the TII QPU156. It defines the instruments, their types, and how they are connected. Modify this according to your actual hardware setup.
    config_type = "quantify_scheduler.backends.qblox_backend.QbloxHardwareCompilationConfig",
    hardware_description = {
        "cluster0": ClusterDescription(
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
        )
    },
    hardware_options = QbloxHardwareOptions(
        latency_corrections={
            f"q{i}:mw-q{i}.01": 0e-9 for i in range(5)
        },
        modulation_frequencies= {
            # e.g "q0:res-q0.ro": {"lo_freq": 7.26e9}, ...
            **{
                f"q{i}:{tipo1}-q{i}.{tipo2}":
                    ModulationFrequencies(lo_freq=7.26e9) if tipo1 == "res" and tipo2 == "ro" else
                    ModulationFrequencies(lo_freq=3.9e9 + i * 0.2e9)
                for (tipo1, tipo2) in [("res", "ro"), ("mw", "01"), ("mw", "12")]
                for i in range(5)
            },
            "f0:in-f0.ro": ModulationFrequencies(lo_freq=7.26e9),
        }, 
        output_att={
            "cluster0.module20.complex_output_0": OutputAttenuation(36),
            "cluster0.module14.complex_output_1": OutputAttenuation(10),
            "cluster0.module6.complex_output_0": OutputAttenuation(10),
            "cluster0.module6.complex_output_1": OutputAttenuation(10),
            "cluster0.module12.complex_output_0": OutputAttenuation(10),
            "cluster0.module12.complex_output_1": OutputAttenuation(10),
        },
        input_gain={
            "cluster0.module20.complex_input_0": ComplexInputGain(gain_I=0, gain_Q=0),  # Gain in dB for the return signal
        },
        input_att = None,
        mixer_corrections={
            f"q{i}:{t1}-q{i}.{t2}": QbloxMixerCorrections() 
            for (t1, t2) in [("res", "ro"), ("mw", "01")]
            for i in range(5)
        },
        # Distortions correction for flux lines (example, modify as needed)
        # distortion_corrections = {
        #     f"q{i}:fl-cl0.baseband": QbloxHardwareDistortionCorrection(
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
            ("cluster0.module20.complex_input_0", ["q0:res", "q1:res","q2:res","q3:res","q4:res"]), # Probe path
            ("cluster0.module20.complex_output_0", "f0:in"), # Feedback path
        ]}
    ).model_dump(),
)

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
globals()[cluster_name] = setup_cluster(cluster_name, CLUSTER_IP)

# -- Hardware abstraction layer --
instrument_coordinator = setup_instrument_coordinator(clusters=[globals()[cluster_name]])

# -- Utility instruments --
meas_ctrl, nested_meas_ctrl = setup_utilities()

# -- Quantum device --
_hw_cfg_path = Path(os.environ.get("HDW_CNFG_DIR", Path.home() / "shared" / "device_configs")) / f"{platform_name}_config.json"
quantum_device = setup_device(
    platform_name=platform_name,
    hw_config=HARDWARE_CFG_TII,
    hw_config_path=_hw_cfg_path if (_hw_cfg_path.exists() and load_from_file) else None,
    meas_ctrl=meas_ctrl,
    nested_meas_ctrl=nested_meas_ctrl,
    instrument_coordinator=instrument_coordinator,
)

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