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

from quantify_scheduler.backends.types.qblox import ComplexChannelDescription
from quantify_scheduler.backends.qblox.enums import DistortionCorrectionLatencyEnum, LoCalEnum, SidebandCalEnum

drive_modules = ["6", "12", "14"]
probe_module = ["20"]
num_qubits = 5

HW_CONFIG_DICT = {
    'config_type' : "quantify_scheduler.backends.qblox_backend.QbloxHardwareCompilationConfig",
    **QbloxHardwareCompilationConfig(
        hardware_description = {
            "cluster0": ClusterDescription(
                instrument_type="Cluster",
                ref="internal", # The reference source for the instrument.
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
            latency_corrections={
                f"q{i}:mw-q{i}.01": 0e-9 for i in range(num_qubits)
            },
            modulation_frequencies= {
                # e.g "q0:res-q0.ro": {"lo_freq": 7.26e9}, ...
                **{
                    f"q{i}:{tipo1}-q{i}.{tipo2}":
                        ModulationFrequencies(lo_freq=7.26e9) if tipo1 == "res" and tipo2 == "ro" else
                        ModulationFrequencies(lo_freq=3.9e9 + i * 0.2e9)
                    for (tipo1, tipo2) in [("res", "ro"), ("mw", "01"), ("mw", "12")]
                    for i in range(num_qubits)
                },
                "f0:in-f0.ro": ModulationFrequencies(lo_freq=7.26e9),
            }, 
            output_att={
                **{
                    f"cluster0.module{slot}.complex_output_{i}": 10 for slot in drive_modules for i in range(2)
                },
                **{
                    f"cluster0.module{slot}.complex_output_0": 36 for slot in probe_module
                },
            },
            input_gain={
                "cluster0.module20.complex_input_0": ComplexInputGain(gain_I=0, gain_Q=0),  # Gain in dB for the return signal
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
        connectivity = Connectivity.model_validate(
            connectivity_dict := {"graph":[
                ("cluster0.module14.complex_output_1", "q0:mw"),
                ("cluster0.module6.complex_output_1", "q1:mw"),
                ("cluster0.module6.complex_output_0", "q2:mw"),
                ("cluster0.module12.complex_output_0", "q3:mw"),
                ("cluster0.module12.complex_output_1", "q4:mw"),
                ("cluster0.module20.complex_output_0", ["q0:res", "q1:res", "q2:res", "q3:res", "q4:res"]),  # Probe TX path
                ("cluster0.module20.complex_output_0",  "f0:in"),   # Feedline RX path (on TX port)
            ]}
        ).model_dump()
    ).model_dump()
}