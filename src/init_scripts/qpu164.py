"""
Initialization script for TII QPU164.

Author: Juan Villegas, TII QRC
Version: 1.0
Date: 2026-04-03

This script sets up the hardware configuration, instrument connections, and quantum
device representation for the TII QPU164. Platform-specific constants are defined at
the top; shared boilerplate is delegated to :mod:`init_scripts._common`.
"""

# Import pydantic models for hardware configuration
from init_scripts._common import (
    # pydantic models for hardware configuration
    QbloxHardwareCompilationConfig,
    ClusterSettings, AnalogModuleSettings, RFModuleSettings, Connectivity,
    QbloxHardwareDescription, ClusterDescription, ClusterModuleDescription, QbloxHardwareOptions,
    # pydantic models for parameters
    ModulationFrequencies, QbloxHardwareDistortionCorrection, QbloxMixerCorrections, ComplexInputGain, InputAttenuation, OutputAttenuation,
    # qblox module types
    QRMDescription, QCMDescription, QRMRFDescription, QCMRFDescription, QTMDescription,
)

CLUSTER_IP    = "192.168.0.20"  # IP address of the cluster.
PLATFORM_NAME = "qpu164"        # Used for the data directory and device config file name.
LOAD_CFG_FILE = False            # Set True to load hardware config from the saved JSON file.

HARDWARE_CFG_TII = QbloxHardwareCompilationConfig(
    config_type = "quantify_scheduler.backends.qblox_backend.QbloxHardwareCompilationConfig",
    hardware_description = {
        "cluster0": ClusterDescription(
            instrument_type="Cluster",
            ip=CLUSTER_IP,
            ref="internal",
            sequence_to_file=False,
            modules={
                "10": QCMRFDescription(),
                "12": QCMRFDescription(),
                "14": QCMRFDescription(),
                "18": QRMRFDescription(),
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
                    ModulationFrequencies(lo_freq=7.029e9) if tipo1 == "res" and tipo2 == "ro" else
                    ModulationFrequencies(lo_freq=4.75e9 + i * 0.3e9)
                for (tipo1, tipo2) in [("res", "ro"), ("mw", "01"), ("mw", "12")]
                for i in range(5)
            },
            "f0:in-f0.ro": ModulationFrequencies(lo_freq=7.029e9),
        }, 
        output_att={
            "cluster0.module18.complex_output_0": OutputAttenuation(20),
            "cluster0.module10.complex_output_0": OutputAttenuation(20),
            "cluster0.module10.complex_output_1": OutputAttenuation(4),
            "cluster0.module12.complex_output_0": OutputAttenuation(4),
            "cluster0.module12.complex_output_1": OutputAttenuation(4),
            "cluster0.module14.complex_output_1": OutputAttenuation(4),
        },
        input_gain={
            "cluster0.module18.complex_input_0": ComplexInputGain(gain_I=0, gain_Q=0),
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
        {"graph": [
            ("cluster0.module10.complex_output_0", "q0:mw"),
            ("cluster0.module10.complex_output_1", "q1:mw"),
            ("cluster0.module12.complex_output_0", "q2:mw"),
            ("cluster0.module12.complex_output_1", "q3:mw"),
            ("cluster0.module14.complex_output_1", "q4:mw"),
            ("cluster0.module18.complex_input_0",  ["q0:res", "q1:res", "q2:res", "q3:res", "q4:res"]),  # Probe path
            ("cluster0.module18.complex_output_0", "f0:in"),  # Feedback path
        ]}
    ).model_dump(),
)

############################################
# 1. Imports
############################################

from init_scripts._common import (
    # stdlib
    os, logging, time, Path, reload, suppress,
    # numeric / visualization
    np, plt, nx, display, SVG,
    # instruments
    Instrument, Cluster, qblox,
    # quantify (quantify_core fallback handled in _common)
    pqm, get_datadir, set_datadir, load_settings_onto_instrument, InstrumentMonitor,
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
set_datadir(_cal_data_dir) # Set quantify data directory to the platform-specific calibration directory
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
_hw_cfg_path = Path(os.environ.get("HDW_CNFG_DIR", Path.home() / "shared" / "device_configs")) / f"{platform_name}_config.json"
quantum_device = setup_device(
    platform_name=platform_name,
    hw_config=HARDWARE_CFG_TII,
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
