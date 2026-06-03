HW_CONFIG_DICT = {
    'config_type': 'quantify_scheduler.backends.qblox_backend.QbloxHardwareCompilationConfig',
    'hardware_description': {
        'cluster0': {
            'instrument_type': 'Cluster',
            'ref': 'internal',
            'modules': {
                '2': {
                    'instrument_type': 'QCM',
                    'real_output_2': {'distortion_correction_latency_compensation': 30},
                    'real_output_1': {'distortion_correction_latency_compensation': 30},
                    'real_output_0': {'distortion_correction_latency_compensation': 30},
                    'real_output_3': {'distortion_correction_latency_compensation': 30}
                },
                '4': {
                    'instrument_type': 'QCM',
                    'real_output_0': {'distortion_correction_latency_compensation': 30}
                },
                '6': {'instrument_type': 'QCM'},
                '8': {'instrument_type': 'QCM_RF'},
                '10': {'instrument_type': 'QCM_RF'},
                '12': {'instrument_type': 'QCM_RF'},
                '14': {'instrument_type': 'QCM_RF'},
                '16': {'instrument_type': 'QCM_RF'},
                '18': {'instrument_type': 'QRM_RF'},
                '20': {'instrument_type': 'QRM_RF'}
            }
        }
    },
    'hardware_options': {
        'modulation_frequencies': {
            'q0:res-q0.ro': {'lo_freq': 7541504209.477961},
            'q1:res-q1.ro': {'lo_freq': 7541504209.477961},
            'q2:res-q2.ro': {'lo_freq': 7541504209.477961},
            'q3:res-q3.ro': {'lo_freq': 7541504209.477961},
            'q4:res-q4.ro': {'lo_freq': 7541504209.477961},
            'q0:mw-q0.01': {'lo_freq': 4710413573.637379},
            'q0:mw-q0.12': {'lo_freq': 4710413573.637379},
            'q1:mw-q1.01': {'lo_freq': 4958237221.742168},
            'q1:mw-q1.12': {'lo_freq': 4958237221.742168},
            'q2:mw-q2.01': {'lo_freq': 5466576605.765685},
            'q2:lru-q2.lru': {'lo_freq': 3415873002.4192915},
            'q3:lru-q3.lru': {'lo_freq': 4602058452.016491},
            'q4:lru-q4.lru': {'lo_freq': 4430860839.901677},
            'q2:mw-q2.12': {'lo_freq': 5466576605.765685},
            'q3:mw-q3.01': {'lo_freq': 6275101607.935588},
            'q3:mw-q3.12': {'lo_freq': 6275101607.935588},
            'q4:mw-q4.01': {'lo_freq': 6184017471.664373},
            'q4:mw-q4.12': {'lo_freq': 6184017471.664373}
        },
        'output_att': {
            'q0:res-q0.ro': 30,
            'q1:res-q1.ro': 30,
            'q2:res-q2.ro': 30,
            'q3:res-q3.ro': 30,
            'q4:res-q4.ro': 30,
            'q0:mw-q0.01': 8,
            'q0:mw-q0.12': 8,
            'q1:mw-q1.01': 12,
            'q1:mw-q1.12': 12,
            'q2:mw-q2.01': 8,
            'q2:lru-q2.lru': 0,
            'q3:lru-q3.lru': 0,
            'q4:lru-q4.lru': 0,
            'q2:mw-q2.12': 8,
            'q3:mw-q3.01': 6,
            'q3:mw-q3.12': 6,
            'q4:mw-q4.01': 8,
            'q4:mw-q4.12': 8,
            'q0:mw-q4.01': 10,
            'q0:mw-q4.12': 10,
            'f0:in-f0.ro': 10,
            'q1iso:res-q1iso.ro': 46,
            'q1iso:mw-q1iso.01': 0,
            'q1iso:mw-q1iso.12': 0,
            'q0iso:res-q0iso.ro': 50,
            'q0iso:mw-q0iso.01': 0,
            'q0iso:mw-q0iso.12': 0
        },
        'mixer_corrections': {
            'q0:mw-q0.01': {
                'auto_lo_cal': 'on_lo_interm_freq_change',
                'auto_sideband_cal': 'off',
                'dc_offset_i': None,
                'dc_offset_q': None,
                'amp_ratio': 0.8305345773696899,
                'phase_error': -22.493698120117188
            },
            'q0:mw-q0.12': {
                'auto_lo_cal': 'on_lo_interm_freq_change',
                'auto_sideband_cal': 'on_interm_freq_change',
                'dc_offset_i': None,
                'dc_offset_q': None,
                'amp_ratio': 1.0,
                'phase_error': 0.0
            },
            'q0:res-q0.ro': {
                'auto_lo_cal': 'on_lo_interm_freq_change',
                'auto_sideband_cal': 'on_interm_freq_change',
                'dc_offset_i': None,
                'dc_offset_q': None,
                'amp_ratio': 1.0,
                'phase_error': 0.0
            },
            'q1:mw-q1.01': {
                'auto_lo_cal': 'on_lo_interm_freq_change',
                'auto_sideband_cal': 'off',
                'dc_offset_i': None,
                'dc_offset_q': None,
                'amp_ratio': 1.1027047634124756,
                'phase_error': -13.599453926086426
            },
            'q1:mw-q1.12': {
                'auto_lo_cal': 'on_lo_interm_freq_change',
                'auto_sideband_cal': 'on_interm_freq_change',
                'dc_offset_i': None,
                'dc_offset_q': None,
                'amp_ratio': 1.0,
                'phase_error': 0.0
            },
            'q1:res-q1.ro': {
                'auto_lo_cal': 'on_lo_interm_freq_change',
                'auto_sideband_cal': 'on_interm_freq_change',
                'dc_offset_i': None,
                'dc_offset_q': None,
                'amp_ratio': 1.0,
                'phase_error': 0.0
            },
            'q2:mw-q2.01': {
                'auto_lo_cal': 'on_lo_interm_freq_change',
                'auto_sideband_cal': 'off',
                'dc_offset_i': None,
                'dc_offset_q': None,
                'amp_ratio': 0.9302040934562683,
                'phase_error': -23.161396026611328
            },
            'q2:mw-q2.12': {
                'auto_lo_cal': 'on_lo_interm_freq_change',
                'auto_sideband_cal': 'on_interm_freq_change',
                'dc_offset_i': None,
                'dc_offset_q': None,
                'amp_ratio': 1.0,
                'phase_error': 0.0
            },
            'q2:res-q2.ro': {
                'auto_lo_cal': 'on_lo_interm_freq_change',
                'auto_sideband_cal': 'on_interm_freq_change',
                'dc_offset_i': None,
                'dc_offset_q': None,
                'amp_ratio': 1.0,
                'phase_error': 0.0
            },
            'q3:mw-q3.01': {
                'auto_lo_cal': 'on_lo_interm_freq_change',
                'auto_sideband_cal': 'off',
                'dc_offset_i': None,
                'dc_offset_q': None,
                'amp_ratio': 0.9746190309524536,
                'phase_error': 0.8550974130630493
            },
            'q3:mw-q3.12': {
                'auto_lo_cal': 'on_lo_interm_freq_change',
                'auto_sideband_cal': 'on_interm_freq_change',
                'dc_offset_i': None,
                'dc_offset_q': None,
                'amp_ratio': 1.0,
                'phase_error': 0.0
            },
            'q3:res-q3.ro': {
                'auto_lo_cal': 'on_lo_interm_freq_change',
                'auto_sideband_cal': 'on_interm_freq_change',
                'dc_offset_i': None,
                'dc_offset_q': None,
                'amp_ratio': 1.0,
                'phase_error': 0.0
            },
            'q4:mw-q4.01': {
                'auto_lo_cal': 'on_lo_interm_freq_change',
                'auto_sideband_cal': 'off',
                'dc_offset_i': None,
                'dc_offset_q': None,
                'amp_ratio': 0.9605964422225952,
                'phase_error': -4.866887092590332
            },
            'q4:mw-q4.12': {
                'auto_lo_cal': 'on_lo_interm_freq_change',
                'auto_sideband_cal': 'on_interm_freq_change',
                'dc_offset_i': None,
                'dc_offset_q': None,
                'amp_ratio': 1.0,
                'phase_error': 0.0
            },
            'q4:res-q4.ro': {
                'auto_lo_cal': 'on_lo_interm_freq_change',
                'auto_sideband_cal': 'on_interm_freq_change',
                'dc_offset_i': None,
                'dc_offset_q': None,
                'amp_ratio': 1.0,
                'phase_error': 0.0
            },
            'f0:in-f0.ro': {
                'auto_lo_cal': 'on_lo_interm_freq_change',
                'auto_sideband_cal': 'on_interm_freq_change',
                'dc_offset_i': None,
                'dc_offset_q': None
            }
        },
        'latency_corrections': {
            'q1:mw-q1.01': 0.0,
            'q1:mw-q1.12': 0.0,
            'q2:mw-q2.01': 0.0,
            'q2:mw-q2.12': 0.0,
            'q0:mw-q0.01': 0.0,
            'q0:mw-q0.12': 0.0,
            'q3:mw-q3.01': 0.0,
            'q3:mw-q3.12': 0.0,
            'q2:fl-cl0.baseband': -3.26e-07,
            'q4:fl-cl0.baseband': -3.24e-07,
            'q0:fl-cl0.baseband': -3.2e-07,
            'q1:fl-cl0.baseband': -3.24e-07,
            'q3:fl-cl0.baseband': -3.3e-07,
            'q4:mw-q4.01': 0.0,
            'q4:mw-q4.12': 0.0
        },
        'distortion_corrections': {}
    },
    'connectivity': {
        'graph': [
            ['cluster0.module8.complex_output_0', 'q0:mw'],
            ['cluster0.module8.complex_output_1', 'q1:mw'],
            ['cluster0.module10.complex_output_0', 'q2:mw'],
            ['cluster0.module10.complex_output_1', 'q2:lru'],
            ['cluster0.module14.complex_output_0', 'q4:lru'],
            ['cluster0.module14.complex_output_1', 'q3:lru'],
            ['cluster0.module12.complex_output_1', 'q3:mw'],
            ['cluster0.module12.complex_output_0', 'q4:mw'],
            ['cluster0.module18.complex_output_0', 'q0:res'],
            ['cluster0.module18.complex_output_0', 'q1:res'],
            ['cluster0.module18.complex_output_0', 'q2:res'],
            ['cluster0.module18.complex_output_0', 'q3:res'],
            ['cluster0.module18.complex_output_0', 'q4:res'],
            ['cluster0.module18.complex_output_0', 'f0:in'],
            ['cluster0.module2.real_output_0', 'q0:fl'],
            ['cluster0.module2.real_output_1', 'q1:fl'],
            ['cluster0.module2.real_output_2', 'q2:fl'],
            ['cluster0.module2.real_output_3', 'q3:fl'],
            ['cluster0.module4.real_output_0', 'q4:fl']
        ]
    }
}