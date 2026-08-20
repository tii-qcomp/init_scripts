# ---------------------------------------------------------------------------
# Quantify Pydantic Types
# ---------------------------------------------------------------------------
from quantify.backends.types.common import Connectivity, ModulationFrequencies
from quantify.backends.qblox_scheduler.types import QbloxHardwareDescription, QbloxMixerCorrections, QbloxRealInputGain
from quantify.backends.qblox_scheduler import QbloxSchedulerHardwareCompilationConfig
from quantify.backends.qblox_scheduler import QbloxHardwareOptions

from qblox_scheduler.backends.types.qblox import (
    QRMDescription, QCMDescription, QRMRFDescription, QCMRFDescription, QTMDescription, 
)
from qblox_scheduler.backends.types.qblox import ComplexChannelDescription
from qblox_scheduler.backends.qblox.enums import DistortionCorrectionLatencyEnum, LoCalEnum, SidebandCalEnum
from superconducting_qubit_tools.backends.hardware_description import QbloxHardwareCompilationConfig
drive_modules = ["8", "10", "12", "14"]
probe_module = ["18", "20"]
num_qubits = 8

HW_CONFIG_DICT = {
    'config_type' : "superconducting_qubit_tools.backends.hardware_description.QbloxHardwareCompilationConfig",
    **QbloxHardwareCompilationConfig(
        hardware_description = {
            "cluster0": QbloxHardwareDescription(
                instrument_type="Cluster",
                ref="internal", # The reference source for the instrument.
                ip = ,
                sequence_to_file=False, # Write sequencer programs to files for (all modules in this) instrument.
                modules={
                    **{f"{slot}": QCMRFDescription(complex_output_0=ComplexChannelDescription(distortion_correction_latency_compensation=DistortionCorrectionLatencyEnum.NO_DELAY_COMP),
                                           complex_output_1=ComplexChannelDescription(distortion_correction_latency_compensation=DistortionCorrectionLatencyEnum.NO_DELAY_COMP))
                       for slot in drive_modules # QCMRF Modules
                    },
                    **{f"{slot}": QRMRFDescription(complex_output_0 = ComplexChannelDescription(distortion_correction_latency_compensation = DistortionCorrectionLatencyEnum.NO_DELAY_COMP), 
                                           complex_input_0 = ComplexChannelDescription(distortion_correction_latency_compensation = DistortionCorrectionLatencyEnum.NO_DELAY_COMP))
                       for slot in probe_module # QRMRF Modules
                    },
                }
            )
        },
        hardware_options = QbloxHardwareOptions(
            latency_corrections={},
            modulation_frequencies= {
                # e.g "q0:res-q0.ro": {"lo_freq": 7.26e9}, ...
                **{
                    f"q{i}:{tipo1}-q{i}.{tipo2}":
                        ModulationFrequencies(lo_freq=7.1e9) if tipo1 == "res" and tipo2 == "ro" else
                        ModulationFrequencies(lo_freq=3.9e9 + i * 0.2e9)
                    for (tipo1, tipo2) in [("res", "ro"), ("mw", "01"), ("mw", "12")]
                    for i in range(num_qubits)
                },
                "f0:in-f0.ro": ModulationFrequencies(lo_freq=7.1e9),
                "f1:in-f1.ro": ModulationFrequencies(lo_freq=7.26e9),
            }, 
            output_att={
                # e.g "q0:res-q0.ro": 36, ...
                **{
                    f"q{i}:{tipo1}-q{i}.{tipo2}": 36 if tipo1 == "res" and tipo2 == "ro" else 10
                    for (tipo1, tipo2) in [("res", "ro"), ("mw", "01"), ("mw", "12")]
                    for i in range(num_qubits)
                },
            },
            input_gain={
                # e.g "q0:res-q0.ro": {'gain_I':0, 'gain_Q':0), ...
                f"q{i}:{tipo1}-q{i}.{tipo2}": QbloxRealInputGain(gain_I=0, gain_Q=0)
                for (tipo1, tipo2) in [("res", "ro")]
                for i in range(num_qubits)
            },
            mixer_corrections={
                f"q{i}:{t1}-q{i}.{t2}": QbloxMixerCorrections(
                    dc_offset_i = 0.0,
                    dc_offset_q = 0.0,
                    amp_ratio = 1.0,
                    phase_error = 0.0,
                    auto_lo_cal= LoCalEnum.OFF , #"on_lo_interm_freq_change",
                    auto_sideband_cal= SidebandCalEnum.OFF , #"on_interm_freq_change"
                ) 
                for (t1, t2) in [("res", "ro"), ("mw", "01"), ("mw", "12")]
                for i in range(num_qubits)
            },
            # Parameters not defined nedd to be set as {} to avoid errors
            input_att = {},
            sequencer_options = {}, 
            digitization_thresholds = {},
            crosstalk = {}, 
            distortion_corrections = {}, 
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
            #         ) for i in range(num_qubits)
            # },
        ),
        connectivity=Connectivity.model_validate(
            {"graph": [
                ("cluster.module14.complex_output_0", "q0:mw"),
                ("cluster.module14.complex_output_1", "q1:mw"),
                ("cluster.module12.complex_output_0", "q2:mw"),
                ("cluster.module12.complex_output_1", "q3:mw"),
                ("cluster.module10.complex_output_0", "q4:mw"),
                ("cluster.module10.complex_output_1", "q5:mw"),
                ("cluster.module8.complex_output_0", "q6:mw"),
                ("cluster.module8.complex_output_1", "q7:mw"),
                ("cluster.module18.complex_output_0", "q0:res"),
                ("cluster.module18.complex_output_0", "q1:res"),
                ("cluster.module18.complex_output_0", "q2:res"),
                ("cluster.module18.complex_output_0", "q3:res"),
                ("cluster.module20.complex_output_0", "q4:res"),
                ("cluster.module20.complex_output_0", "q5:res"),
                ("cluster.module20.complex_output_0", "q6:res"),
                ("cluster.module20.complex_output_0", "q7:res"),
                ("cluster.module20.complex_output_0", "f1:in"),
                ("cluster.module18.complex_output_0", "f0:in"),
            ]}
        ).model_dump(),
    ).model_dump(),
}

# HW_CONFIG_DICT = {
#     'config_type': 'superconducting_qubit_tools.backends.hardware_description.QbloxHardwareCompilationConfig',
#     'hardware_description': {
#          'cluster': {
#                'instrument_type': 'Cluster',
#                'ref': 'internal',
#                'ip': '192.168.0.22',
#                'sequence_to_file': False,
#                'modules': {
#                     '8': {'instrument_type': 'QCM_RF',},
#                     '10': {'instrument_type': 'QCM_RF',},
#                     '12': {'instrument_type': 'QCM_RF',},
#                     '14': {'instrument_type': 'QCM_RF',},
#                     '18': {'instrument_type': 'QRM_RF',},
#                     '20': {'instrument_type': 'QRM_RF',}
#                 }                                
#           }
#      },
#      'hardware_options': {
#           'crosstalk': {},
#           'latency_corrections': {},
#           'distortion_corrections': {},
#           'modulation_frequencies': {
#               'q0:res-q0.ro': {'interm_freq': None, 'lo_freq': 7100000000.0},
#                'q1:res-q1.ro': {'interm_freq': None, 'lo_freq': 7100000000.0},
#                'q2:res-q2.ro': {'interm_freq': None, 'lo_freq': 7100000000.0},
#                'q3:res-q3.ro': {'interm_freq': None, 'lo_freq': 7100000000.0},
#                'q4:res-q4.ro': {'interm_freq': None, 'lo_freq': 7100000000.0},
#                'q5:res-q5.ro': {'interm_freq': None, 'lo_freq': 7100000000.0},
#                'q6:res-q6.ro': {'interm_freq': None, 'lo_freq': 7100000000.0},
#                'q7:res-q7.ro': {'interm_freq': None, 'lo_freq': 7100000000.0},
#                'q0:mw-q0.01': {'interm_freq': None, 'lo_freq': 3900000000.0},
#                'q1:mw-q1.01': {'interm_freq': None, 'lo_freq': 4100000000.0},
#                'q2:mw-q2.01': {'interm_freq': None, 'lo_freq': 4300000000.0},
#                'q3:mw-q3.01': {'interm_freq': None, 'lo_freq': 4500000000.0},
#                'q4:mw-q4.01': {'interm_freq': None, 'lo_freq': 4700000000.0},
#                'q5:mw-q5.01': {'interm_freq': None, 'lo_freq': 4900000000.0},
#                'q6:mw-q6.01': {'interm_freq': None, 'lo_freq': 5100000000.0},
#                'q7:mw-q7.01': {'interm_freq': None, 'lo_freq': 5300000000.0},
#                'q0:mw-q0.12': {'interm_freq': None, 'lo_freq': 3900000000.0},
#                'q1:mw-q1.12': {'interm_freq': None, 'lo_freq': 4100000000.0},
#                'q2:mw-q2.12': {'interm_freq': None, 'lo_freq': 4300000000.0},
#                'q3:mw-q3.12': {'interm_freq': None, 'lo_freq': 4500000000.0},
#                'q4:mw-q4.12': {'interm_freq': None, 'lo_freq': 4700000000.0},
#                'q5:mw-q5.12': {'interm_freq': None, 'lo_freq': 4900000000.0},
#                'q6:mw-q6.12': {'interm_freq': None, 'lo_freq': 5100000000.0},
#                'q7:mw-q7.12': {'interm_freq': None, 'lo_freq': 5300000000.0},
#                'f0:in-f0.ro': {'interm_freq': None, 'lo_freq': 7100000000.0},
#                'f1:in-f1.ro': {'interm_freq': None, 'lo_freq': 7260000000.0}
#           },  
#           'output_att': {
#                'q0:mw-q0.01': 10,
#                'q1:mw-q1.01': 10,
#                'q2:mw-q2.01': 10,
#                'q3:mw-q3.01': 10,
#                'q4:mw-q4.01': 10,
#                'q5:mw-q5.01': 10,
#                'q6:mw-q6.01': 10,
#                'q7:mw-q7.01': 10,
#                'q0:res-q0.ro': 36,
#                'q4:res-q4.ro': 36},
#           'input_gain': {
#                'q0:res-q0.ro': {'gain_I': 0.0, 'gain_Q': 0.0},
#                'q4:res-q4.ro': {'gain_I': 0.0, 'gain_Q': 0.0}
#           },
#      },
#      'connectivity': {
#          'graph': [('cluster.module14.complex_output_0', 'q0:mw'),
#                ('cluster.module14.complex_output_1', 'q1:mw'),
#                ('cluster.module12.complex_output_0', 'q2:mw'),
#                ('cluster.module12.complex_output_1', 'q3:mw'),
#                ('cluster.module10.complex_output_0', 'q4:mw'),
#                ('cluster.module10.complex_output_1', 'q5:mw'),
#                ('cluster.module8.complex_output_0', 'q6:mw'),
#                ('cluster.module8.complex_output_1', 'q7:mw'),
#                ('cluster.module18.complex_output_0', 'q0:res'),
#                ('cluster.module18.complex_output_0', 'q1:res'),
#                ('cluster.module18.complex_output_0', 'q2:res'),
#                ('cluster.module18.complex_output_0', 'q3:res'),
#                ('cluster.module18.complex_output_0', 'f0:in'),
#                ('cluster.module20.complex_output_0', 'q4:res'),
#                ('cluster.module20.complex_output_0', 'q5:res'),
#                ('cluster.module20.complex_output_0', 'q6:res'),
#                ('cluster.module20.complex_output_0', 'q7:res'),
#                ('cluster.module20.complex_output_0', 'f1:in')]
#      },
# }