#!/usr/bin/env python3
"""EPC Gen2 UHF RFID Reader — USRP B210 + Bolton Long Ranger.

Adapted from nkargas/Gen2-UHF-RFID-Reader for the Ettus B210
with a Bolton Long Ranger parabolic antenna (600 MHz – 6.5 GHz).

Usage:
    /usr/bin/python3 apps/reader_b210.py [--rx-only]

The B210 has independent TX/RX RF chains with 0–89.8 dB gain on TX
and 0–76 dB gain on RX. With a single antenna, connect to TX/RX for
full TX+RX (uses ATR switching), or use --rx-only for passive
eavesdropping on RX2 near an existing commercial reader.

Frequency plan: 902–928 MHz US ISM band (FCC Part 15.247).
Default center: 915 MHz.
"""

import argparse
import os
import signal
import sys

from gnuradio import gr, uhd, blocks, filter
from gnuradio import rfid

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(REPO_DIR, "misc", "data")


class rfid_reader_b210(gr.top_block):
    def __init__(self, rx_only=False, freq=915e6, rx_gain=40, tx_gain=60,
                 ampl=0.7, debug_sinks=False):
        gr.top_block.__init__(self, "RFID Reader B210")

        # Radio parameters
        self.adc_rate = 2e6          # 2 MS/s (same as N210 original)
        self.dac_rate = 1e6          # 1 MS/s DAC rate
        self.decim = 5               # Decimation factor
        self.freq = freq
        self.rx_gain = rx_gain
        self.tx_gain = tx_gain
        self.ampl = ampl
        self.rx_only = rx_only

        sample_rate = int(self.adc_rate / self.decim)  # 400 kHz

        # Matched filter: 25 taps at adc_rate, half-symbol at BLF=40kHz
        self.num_taps = [1] * 25

        # --- USRP B210 Source (RX) ---
        self.source = uhd.usrp_source(
            device_addr="type=b200",
            stream_args=uhd.stream_args(
                cpu_format="fc32",
                channels=[0],
            ),
        )
        self.source.set_samp_rate(self.adc_rate)
        self.source.set_center_freq(self.freq, 0)
        self.source.set_gain(self.rx_gain, 0)
        self.source.set_auto_dc_offset(False)

        if rx_only:
            # Passive eavesdrop: listen on RX2 near an existing reader
            self.source.set_antenna("RX2", 0)
            print(f"RX-only mode: antenna=RX2, freq={self.freq/1e6:.1f} MHz, "
                  f"gain={self.rx_gain} dB")
        else:
            # Full TX+RX: single antenna on TX/RX with ATR switching
            self.source.set_antenna("TX/RX", 0)
            print(f"TX+RX mode: antenna=TX/RX, freq={self.freq/1e6:.1f} MHz, "
                  f"rx_gain={self.rx_gain} dB, tx_gain={self.tx_gain} dB")

        # --- Signal processing blocks ---
        self.matched_filter = filter.fir_filter_ccc(self.decim, self.num_taps)
        self.gate = rfid.gate(sample_rate)
        self.tag_decoder = rfid.tag_decoder(sample_rate)
        self.reader = rfid.reader(sample_rate, int(self.dac_rate))
        self.amp = blocks.multiply_const_ff(self.ampl)
        self.to_complex = blocks.float_to_complex()

        # --- Connections: RX path ---
        self.connect(self.source, self.matched_filter)
        self.connect(self.matched_filter, self.gate)
        self.connect(self.gate, self.tag_decoder)
        self.connect((self.tag_decoder, 0), self.reader)
        self.connect(self.reader, self.amp)
        self.connect(self.amp, self.to_complex)

        if rx_only:
            # No TX — sink the reader output to null
            self.null_sink = blocks.null_sink(gr.sizeof_gr_complex)
            self.connect(self.to_complex, self.null_sink)
        else:
            # --- USRP B210 Sink (TX) ---
            self.sink = uhd.usrp_sink(
                device_addr="type=b200",
                stream_args=uhd.stream_args(
                    cpu_format="fc32",
                    channels=[0],
                ),
            )
            self.sink.set_samp_rate(self.dac_rate)
            self.sink.set_center_freq(self.freq, 0)
            self.sink.set_gain(self.tx_gain, 0)
            self.sink.set_antenna("TX/RX", 0)
            self.connect(self.to_complex, self.sink)

        # --- Debug file sinks ---
        if debug_sinks:
            os.makedirs(DATA_DIR, exist_ok=True)
            self.connect(
                (self.tag_decoder, 1),
                blocks.file_sink(
                    gr.sizeof_gr_complex,
                    os.path.join(DATA_DIR, "decoder_b210"),
                    False,
                ),
            )
        else:
            # Decoder debug port must be connected somewhere
            self.connect(
                (self.tag_decoder, 1),
                blocks.null_sink(gr.sizeof_gr_complex),
            )


def main():
    parser = argparse.ArgumentParser(
        description="EPC Gen2 UHF RFID Reader — USRP B210"
    )
    parser.add_argument(
        "--rx-only", action="store_true",
        help="Passive eavesdrop on RX2 (no TX, use near an existing reader)"
    )
    parser.add_argument(
        "--freq", type=float, default=915e6,
        help="Center frequency in Hz (default: 915 MHz)"
    )
    parser.add_argument(
        "--rx-gain", type=float, default=40,
        help="RX gain in dB (default: 40, range: 0–76)"
    )
    parser.add_argument(
        "--tx-gain", type=float, default=60,
        help="TX gain in dB (default: 60, range: 0–89.8)"
    )
    parser.add_argument(
        "--ampl", type=float, default=0.7,
        help="TX output amplitude (default: 0.7, range: 0–1)"
    )
    parser.add_argument(
        "--debug", action="store_true",
        help="Enable debug file sinks in misc/data/"
    )
    args = parser.parse_args()

    print("=== EPC Gen2 UHF RFID Reader — B210 + Bolton Long Ranger ===")
    print(f"Frequency: {args.freq/1e6:.1f} MHz")

    tb = rfid_reader_b210(
        rx_only=args.rx_only,
        freq=args.freq,
        rx_gain=args.rx_gain,
        tx_gain=args.tx_gain,
        ampl=args.ampl,
        debug_sinks=args.debug,
    )

    def shutdown(signum, frame):
        print("\nShutting down...")
        tb.reader.print_results()
        tb.stop()
        tb.wait()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    tb.start()

    print("\nReader running. Press Ctrl+C to stop and show results.")
    try:
        tb.wait()
    except KeyboardInterrupt:
        pass

    print("\n=== Results ===")
    tb.reader.print_results()
    tb.stop()


if __name__ == "__main__":
    main()
