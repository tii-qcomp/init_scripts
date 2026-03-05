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

HW_CONFIG_DICT = {
    'config_type': "quantify_scheduler.backends.qblox_backend.QbloxHardwareCompilationConfig",
    **QbloxHardwareCompilationConfig(
        hardware_description={
            "cluster0": ClusterDescription(
                instrument_type="Cluster",
                ref="internal",
                sequence_to_file=False,
                modules={
                    **{f"{slot}": QCMRFDescription(complex_output_0=ComplexChannelDescription(distortion_correction_latency_compensation=DistortionCorrectionLatencyEnum.NO_DELAY_COMP),
                                           complex_output_1=ComplexChannelDescription(distortion_correction_latency_compensation=DistortionCorrectionLatencyEnum.NO_DELAY_COMP))
                       for slot in ["10", "12", "14"]
                    },
                    "18": QRMRFDescription(complex_output_0=ComplexChannelDescription(distortion_correction_latency_compensation=DistortionCorrectionLatencyEnum.NO_DELAY_COMP),
                                           complex_input_0=ComplexChannelDescription(distortion_correction_latency_compensation=DistortionCorrectionLatencyEnum.NO_DELAY_COMP)),
                },
            )
        },
        hardware_options=QbloxHardwareOptions(
            latency_corrections={
                f"q{i}:mw-q{i}.01": 0e-9 for i in range(5)
            },
            modulation_frequencies={
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
            mixer_corrections={
                f"q{i}:{t1}-q{i}.{t2}": QbloxMixerCorrections(
                    dc_offset_i=0.0,
                    dc_offset_q=0.0,
                    amp_ratio=1.0,
                    phase_error=0.0,
                    auto_lo_cal=LoCalEnum.OFF,
                    auto_sideband_cal=SidebandCalEnum.OFF,
                )
                for (t1, t2) in [("res", "ro"), ("mw", "01")]
                for i in range(5)
            },
            # Parameters not defined need to be set as {} to avoid None being dumped, which causes errors
            input_att = {},
            sequencer_options = {}, 
            digitization_thresholds = {},
            crosstalk = {}, 
            distortion_corrections = {}, 
            # Distortions correction for flux lines (example, modify as needed)
            # distortion_corrections={
            #     f"q{i}:fl-cl0.baseband": QbloxHardwareDistortionCorrection(
            #         filter_func="scipy.signal.lfilter",
            #         input_var_name="x",
            #         kwargs={"b": [0, 0.25, 0.5], "a": [1]},
            #         clipping_values=[-2.5, 2.5]
            #     ) for i in range(5)
            # },
        ),
        connectivity=Connectivity.model_validate(
            {"graph": [
                ("cluster0.module10.complex_output_0", "q0:mw"),
                ("cluster0.module10.complex_output_1", "q1:mw"),
                ("cluster0.module12.complex_output_0", "q2:mw"),
                ("cluster0.module12.complex_output_1", "q3:mw"),
                ("cluster0.module14.complex_output_1", "q4:mw"),
                ("cluster0.module18.complex_output_0", "q0:res"),
                ("cluster0.module18.complex_output_0", "q1:res"),
                ("cluster0.module18.complex_output_0", "q2:res"),
                ("cluster0.module18.complex_output_0", "q3:res"),
                ("cluster0.module18.complex_output_0", "q4:res"),
                ("cluster0.module18.complex_output_0", "f0:in"),
            ]}
        ).model_dump(),
    ).model_dump(),
}
