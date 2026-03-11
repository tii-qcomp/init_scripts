"""
Common imports and utility functions shared across all QPU init scripts.

All generic imports live here so that per-QPU scripts only need a single
``from init_scripts._common import (...)`` block.  The ``quantify`` package
is preferred where available; the code falls back to ``quantify_core``
automatically if it is not installed.
"""

# ---------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------
import logging
import os
import time
import json
from contextlib import suppress
from importlib import reload
from pathlib import Path
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Numeric / Visualization
# ---------------------------------------------------------------------------
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from IPython.display import SVG, display

# ---------------------------------------------------------------------------
# QCoDeS
# ---------------------------------------------------------------------------
from qcodes.instrument.base import Instrument

# ---------------------------------------------------------------------------
# Qblox instruments
# ---------------------------------------------------------------------------
import qblox_instruments as qblox
from qblox_instruments import Cluster

# ---------------------------------------------------------------------------
# Quantify – prefer the `quantify` package, fall back to `quantify_core`
# ---------------------------------------------------------------------------
try:
    import quantify
    from quantify.data.handling import get_datadir, set_datadir
    from quantify.utilities.experiment_helpers import load_settings_onto_instrument
except ImportError as e:
    print("Cannot import quantify, using quantify_core")
    print(e)
    import quantify_core as quantify
    from quantify_core.data.handling import get_datadir, set_datadir
    import quantify_core.visualization.pyqt_plotmon as pqm #Stilll needs to be handled
    from quantify_core.utilities.experiment_helpers import load_settings_onto_instrument
    from quantify_core.visualization.instrument_monitor import InstrumentMonitor #Stilll needs to be handled

import quantify_scheduler

# ---------------------------------------------------------------------------
# Quantify scheduler
# ---------------------------------------------------------------------------
from quantify_scheduler.backends.qblox_backend import constants as qblox_constants
qblox_constants.NUMBER_OF_QBLOX_ACQ_BINS = 2**16
from quantify_scheduler.instrument_coordinator.components.qblox import ClusterComponent
from quantify_scheduler.instrument_coordinator.components.generic import (
    GenericInstrumentCoordinatorComponent,
)
from quantify_scheduler.instrument_coordinator.instrument_coordinator import (
    InstrumentCoordinator,
)
from quantify_scheduler.instrument_coordinator.utility import search_settable_param

# ---------------------------------------------------------------------------
# Quantify Pydantic Types
# ---------------------------------------------------------------------------
from quantify.backends.types.common import ( 
    Connectivity,
)
from quantify_scheduler.backends.types.qblox import (
    ClusterSettings, AnalogModuleSettings, RFModuleSettings,
    QbloxHardwareDescription, ClusterDescription, ClusterModuleDescription, QbloxHardwareOptions,
    QRMDescription, QCMDescription, QRMRFDescription, QCMRFDescription, QTMDescription, 
    QbloxHardwareDistortionCorrection, QbloxMixerCorrections, ComplexInputGain, InputAttenuation, OutputAttenuation 
)
from quantify_scheduler.backends.types.common import (
    ModulationFrequencies
)

from quantify_scheduler.backends.qblox_backend import QbloxHardwareCompilationConfig

# ---------------------------------------------------------------------------
# SCQT
# ---------------------------------------------------------------------------
try: 
    import superconducting_qubit_tools as scqt
    from superconducting_qubit_tools import calibration_functions as cal
    from superconducting_qubit_tools import measurement_functions as meas
    from superconducting_qubit_tools.automation.graph_generation import generate_calibration_graph
    from superconducting_qubit_tools.device_under_test.feedline_element import FeedlineElement
    from superconducting_qubit_tools.device_under_test.quantum_device import QuantumDevice
    from superconducting_qubit_tools.device_under_test.sudden_nz_edge import SuddenNetZeroEdge
    from superconducting_qubit_tools.device_under_test.transmon_element import (
        BasicTransmonElement,
        TransmonElementPurcell,
    )
    from superconducting_qubit_tools.device_under_test.tunable_coupler_transmon_element import (
        TunableCouplerTransmonElement,
    )
except ImportError:
    import warnings
    warnings.warn("superconducting_qubit_tools not found. SCQT-dependent helpers will raise ImportError when called.")
    scqt = cal = meas = generate_calibration_graph = None
    FeedlineElement = SuddenNetZeroEdge = None
    BasicTransmonElement = TransmonElementPurcell = TunableCouplerTransmonElement = None
    try:
        from quantify.device_under_test.quantum_device import QuantumDevice
    except ImportError:
        QuantumDevice = None

try:
    import grace
except ImportError:
    import warnings
    warnings.warn("grace not found. grace-dependent functionality will raise ImportError when called.")
    grace = None

# ---------------------------------------------------------------------------
# OrangeQS / Juice
# ---------------------------------------------------------------------------
try:
    from orangeqs.juice_ext.device_and_instruments import new_run_id
    from orangeqs.juice_ext.device_and_instruments.instrument_monitor import (
        InstrumentMonitorPublisher,
    )
    from orangeqs.juice_ext.device_and_instruments.measurement_control.measurement_control import (
        MeasurementControl,
    )
    from orangeqs.juice_ext.protocol_and_automation.graph import register_calibration_graph
except ImportError:
    import warnings
    warnings.warn("orangeqs.juice_ext not found. OrangeQS/Juice-dependent helpers will raise ImportError when called.")
    new_run_id = InstrumentMonitorPublisher = MeasurementControl = register_calibration_graph = None


# ---------------------------------------------------------------------------
# Instrument setup helpers
# ---------------------------------------------------------------------------

def setup_instrument_coordinator(clusters: list) -> InstrumentCoordinator:
    """
    Return (or create) the singleton InstrumentCoordinator and attach cluster components.

    If an InstrumentCoordinator named ``"instrument_coordinator"`` already exists it is
    reused, avoiding duplicate-instrument errors when a notebook cell is re-run.

    Args:
        clusters: List of :class:`~qblox_instruments.Cluster` instances to add.

    Returns:
        The configured :class:`~quantify_scheduler.instrument_coordinator.InstrumentCoordinator`.
    """
    active_ics = InstrumentCoordinator.instances()
    if len(active_ics) > 0:
        print(f"Running IC: {active_ics}")
        ic_names = [ic.name for ic in active_ics]
        if "instrument_coordinator" in ic_names:
            ic = active_ics[ic_names.index("instrument_coordinator")]
            if not all(cluster.name in ic.components() for cluster in clusters):
                raise RuntimeError(
                    "An InstrumentCoordinator named 'instrument_coordinator' already exists, but it does not contain all the required clusters. This is not handled, please restrat your Kernel."
                )
            else:
                return ic # Reuse existing instance

    instrument_coordinator = InstrumentCoordinator(
        "instrument_coordinator",
        add_default_generic_icc=False,
    )
    ic_clusters = []
    for cluster in clusters:
        ic_cluster = ClusterComponent(cluster)
        ic_clusters.append(ic_cluster)
        instrument_coordinator.add_component(ic_cluster)
    return instrument_coordinator

def setup_utilities() -> tuple:
    """
    Return (or create) the MeasurementControl and nested MeasurementControl singletons.

    Returns:
        Tuple of ``(meas_ctrl, nested_meas_ctrl)``.

    Raises:
        ImportError: If ``orangeqs.juice_ext`` is not installed.
    """
    if MeasurementControl is None:
        raise ImportError(
            "MeasurementControl is not available. Install orangeqs.juice_ext to use setup_utilities()."
        )
    active_mc = MeasurementControl.instances()
    mc_names = [mc.name for mc in active_mc]
    if "meas_ctrl" in mc_names and "nested_meas_ctrl" in mc_names:
        meas_ctrl = active_mc[mc_names.index("meas_ctrl")]
        nested_meas_ctrl = active_mc[mc_names.index("nested_meas_ctrl")]
        return meas_ctrl, nested_meas_ctrl

    meas_ctrl = MeasurementControl("meas_ctrl")
    nested_meas_ctrl = MeasurementControl("nested_meas_ctrl")
    meas_ctrl.attach_plotmon()
    return meas_ctrl, nested_meas_ctrl


def setup_cluster(cluster_name: str, cluster_ip: str) -> Cluster:
    """
    Return (or create) a :class:`~qblox_instruments.Cluster` and enable NCO propagation delay
    compensation on every sequencer.

    Args:
        cluster_name: QCoDeS instrument name, e.g. ``"cluster0"``.
        cluster_ip:   IP address of the cluster, e.g. ``"192.168.0.2"``.

    Returns:
        The connected :class:`~qblox_instruments.Cluster` instance.
    """
    import logging
    logger = logging.getLogger(__name__)

    if cluster_name in Cluster._all_instruments:
        logger.info(f"Cluster '{cluster_name}' already exists — reusing existing instance.")
        return Cluster._all_instruments[cluster_name]

    cluster = Cluster(cluster_name, cluster_ip)
    logger.info(f"{cluster_name} connected: {cluster.get_system_status()}")
    cluster.ext_trigger_input_trigger_address(1) # Typically unused but needs to be set to a valid value (1-15)
    for module in cluster.modules:
        for sequencer in module.sequencers:
            sequencer.nco_prop_delay_comp_en(True)
    return cluster


# ---------------------------------------------------------------------------
# Quantum device setup
# ---------------------------------------------------------------------------

def setup_device(
    platform_name: str,
    hw_config: QbloxHardwareCompilationConfig = {},
    hw_config_path= None,
    meas_ctrl= None,
    nested_meas_ctrl=None,
    instrument_coordinator=None,
) -> QuantumDevice:
    """
    Create (or recreate) the :class:`~superconducting_qubit_tools.device_under_test.quantum_device.QuantumDevice`.

    If a device with the same *platform_name* is already registered it is closed first
    to avoid QCoDeS name conflicts when re-running the init script.

    Args:
        platform_name:          Name used for the QCoDeS instrument and data directory.
        hw_config:              Hardware configuration dict (used when *hw_config_path* is ``None``).
        hw_config_path:         Path to an existing hardware configuration JSON file.
                                When provided, the dict in *hw_config* is ignored.
        meas_ctrl:              :class:`MeasurementControl` instance to attach.
        nested_meas_ctrl:       Nested :class:`MeasurementControl` instance to attach.
        instrument_coordinator: :class:`InstrumentCoordinator` instance to attach.

    Returns:
        The configured :class:`QuantumDevice`.
    """
    # Close any existing instance to avoid name conflicts on re-run
    active_qd = QuantumDevice.instances()
    qd_names = [qd.name for qd in active_qd]
    if platform_name in qd_names:
        qd: QuantumDevice = active_qd[qd_names.index(platform_name)]
        qd.close()

    qd = QuantumDevice(name=platform_name)

    if hw_config_path is not None:
        if isinstance(hw_config_path, str):
            hw_config_path = Path(hw_config_path)
        if not hw_config_path.exists():
            raise FileNotFoundError(f"Hardware config file not found at {hw_config_path}")
        qd.hardware_config.load_from_json_file(hw_config_path)
    else:
        # Normalise to plain dict (handles Pydantic models passed directly)
        if hasattr(hw_config, "model_dump"):
            hw_config = hw_config.model_dump(mode="json")
        # Ensure config_type is present — model_dump() silently drops it but
        # SCQT needs it to identify the Qblox backend when calling
        # generate_hardware_config() internally.
        if isinstance(hw_config, dict) and "config_type" not in hw_config:
            hw_config["config_type"] = (
                "quantify_scheduler.backends.qblox_backend.QbloxHardwareCompilationConfig"
            )
        qd.hardware_config(hw_config)

    qd.instr_measurement_control(meas_ctrl.name if meas_ctrl is not None else None)
    qd.instr_nested_measurement_control(
        nested_meas_ctrl.name if nested_meas_ctrl is not None else None
    )
    qd.instr_instrument_coordinator(
        instrument_coordinator.name if instrument_coordinator is not None else None
    )
    return qd


# ---------------------------------------------------------------------------
# Topology helpers
# ---------------------------------------------------------------------------

def helper_configure_ladder(
    qd, num_qubits: int = 5, feedline_name: str = "f0"
):
    """
    Populate a :class:`QuantumDevice` with a 1-D ladder of transmon qubits sharing
    a single feedline.

    Qubits are named ``q0 … q(num_qubits-1)`` and connected with
    :class:`~superconducting_qubit_tools.device_under_test.sudden_nz_edge.SuddenNetZeroEdge`
    gates between adjacent pairs.

    Args:
        qd:           The quantum device to configure.
        num_qubits:   Number of qubits to add.
        feedline_name: Name for the :class:`FeedlineElement` (default ``"f0"``).

    Returns:
        Tuple ``(qubits, edges, feedline)``.

    Raises:
        ImportError: If ``superconducting_qubit_tools`` is not installed.
    """
    if BasicTransmonElement is None or SuddenNetZeroEdge is None or FeedlineElement is None:
        raise ImportError(
            "SCQT device elements are not available. Install superconducting_qubit_tools to use helper_configure_ladder()."
        )
    qubits, edges = [], []

    for i in range(num_qubits):
        qd.add_element(q := BasicTransmonElement(f"q{i}"))
        qubits.append(q)

    for i in range(num_qubits - 1):
        edge = SuddenNetZeroEdge(
            child_element_name=f"q{i}", parent_element_name=f"q{i + 1}"
        )
        qd.add_edge(edge)
        edges.append(edge)

    qd.add_element(feedline := FeedlineElement(feedline_name))
    qd.add_connection(feedline, [q.ports.readout() for q in qubits])

    return qubits, edges, feedline


def helper_defaults(
    qd: QuantumDevice,
    clocks: list = [],
    readouts: list = [],
) -> None:
    """
    Apply default drive and readout clock frequencies to every qubit in *qd*.

    Frequencies in *clocks* and *readouts* are matched positionally to the qubit
    elements returned by :meth:`QuantumDevice.elements`. If the lists are shorter
    than the number of qubits, fallback values (``4 GHz + i×100 MHz`` and
    ``7 GHz + i×100 MHz``) are used for the remaining qubits.

    Args:
        qd:       The quantum device whose qubits to configure.
        clocks:   Drive frequencies (Hz) per qubit.
        readouts: Readout frequencies (Hz) per qubit.
    """
    for i, obj_name in enumerate(qd.elements()):
        qobj = qd.get_element(obj_name)
        if hasattr(qobj, "is_qubit") and qobj.is_qubit:
            qobj.clock_freqs.f01(clocks[i] if i < len(clocks) else 4e9 + i * 100e6)
            qobj.clock_freqs.readout(
                readouts[i] if i < len(readouts) else 7e9 + i * 100e6
            )
