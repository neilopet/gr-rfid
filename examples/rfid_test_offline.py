#!/usr/bin/env python3
"""Offline RFID test -- no GUI, no hardware.

Runs the EPC Gen2 reader flowgraph against pre-recorded IQ data.
Uses the same signal processing chain as the live reader:
  file_source -> matched_filter -> gate -> tag_decoder -> reader
"""

import os
import sys
import time

from gnuradio import gr, blocks, filter
from gnuradio import rfid

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(REPO_DIR, "misc", "data")


class rfid_test_offline(gr.top_block):
    def __init__(self):
        gr.top_block.__init__(self, "RFID Offline Test")

        # Variables (match original reader.py)
        adc_rate = 2000000          # 2 MS/s complex samples
        dac_rate = 1000000          # 1 MS/s DAC rate
        decim = 5                   # Decimation factor
        ampl = 0.1                  # Output amplitude
        sample_rate = int(adc_rate / decim)  # 400 kHz effective

        # Each FM0 symbol = adc_rate/BLF = 2e6/40e3 = 50 samples
        # After decim=5: 10 samples per symbol
        num_taps = [1] * 25        # Matched filter (half symbol period)

        test_data = os.path.join(DATA_DIR, "file_source_test")
        if not os.path.exists(test_data):
            print(f"ERROR: Test data not found at {test_data}", file=sys.stderr)
            sys.exit(1)

        # Blocks
        self.file_source = blocks.file_source(
            gr.sizeof_gr_complex, test_data, False
        )
        self.matched_filter = filter.fir_filter_ccc(decim, num_taps)
        self.gate = rfid.gate(sample_rate)
        self.tag_decoder = rfid.tag_decoder(sample_rate)
        self.reader = rfid.reader(sample_rate, dac_rate)
        self.amp = blocks.multiply_const_ff(ampl)
        self.to_complex = blocks.float_to_complex()

        # Output sinks
        self.file_sink = blocks.file_sink(
            gr.sizeof_gr_complex,
            os.path.join(DATA_DIR, "file_sink"),
            False,
        )
        self.decoder_sink = blocks.file_sink(
            gr.sizeof_gr_complex,
            os.path.join(DATA_DIR, "decoder"),
            False,
        )

        # Connections (same topology as original reader)
        self.connect(self.file_source, self.matched_filter)
        self.connect(self.matched_filter, self.gate)
        self.connect(self.gate, self.tag_decoder)
        self.connect((self.tag_decoder, 0), self.reader)
        self.connect(self.reader, self.amp)
        self.connect(self.amp, self.to_complex)
        self.connect(self.to_complex, self.file_sink)

        # Decoder debug output (port 1)
        self.connect((self.tag_decoder, 1), self.decoder_sink)


if __name__ == "__main__":
    print("=== EPC Gen2 UHF RFID Offline Test ===")
    print(f"Test data: {os.path.join(DATA_DIR, 'file_source_test')}")

    tb = rfid_test_offline()
    tb.start()

    # The flowgraph has a feedback loop (reader -> gate), so tb.wait()
    # blocks forever. The gate block sets TERMINATED after MAX_NUM_QUERIES
    # but never returns WORK_DONE. Run for a fixed duration then stop.
    time.sleep(10)

    tb.stop()
    tb.wait()

    print("\n=== Results ===")
    tb.reader.print_results()
