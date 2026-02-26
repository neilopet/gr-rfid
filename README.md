# gr-rfid — EPC Gen2 UHF RFID Reader for GNU Radio 3.10

Ported from [EMDCYY/gr-rfid](https://github.com/EMDCYY/gr-rfid) (itself
based on [nkargas/Gen2-UHF-RFID-Reader](https://github.com/nkargas/Gen2-UHF-RFID-Reader)).

## What changed from upstream

- **GNU Radio 3.10** build system (was 3.8)
- **pybind11 bindings** replace SWIG
- Headers moved to `include/gnuradio/rfid/` (GR 3.10 convention)
- `boost::shared_ptr` → `std::shared_ptr`
- GRC YAML files updated for `from gnuradio import rfid`
- New `apps/reader_b210.py` — B210 live reader with CLI
- New `examples/rfid_test_offline.py` — headless offline test

## Tested Environment

- Kali Linux (Debian-based), x86_64
- Python 3.13, GNU Radio 3.10.12, UHD 4.9.0
- USRP B210 + Bolton Long Ranger parabolic antenna (600 MHz – 6.5 GHz)
- OTA confirmed: B210 TX+RX at 915 MHz received tag RN16 backscatter

## Build & Install

```bash
cd gr-rfid
rm -rf build && mkdir build && cd build
cmake -DCMAKE_INSTALL_PREFIX=/usr/local ..
make -j$(nproc)
sudo make install && sudo ldconfig
```

Verify:
```bash
/usr/bin/python3 -c "from gnuradio import rfid; print(dir(rfid))"
```

## Usage

### Offline test (no hardware)

```bash
/usr/bin/python3 examples/rfid_test_offline.py
```

Runs the full EPC Gen2 reader pipeline against pre-recorded IQ data in
`misc/data/file_source_test`.

### B210 live reader

```bash
# Full TX+RX (antenna on TX/RX port)
/usr/bin/python3 apps/reader_b210.py

# Passive eavesdrop (antenna on RX2, near an existing reader)
/usr/bin/python3 apps/reader_b210.py --rx-only

# Custom parameters
/usr/bin/python3 apps/reader_b210.py --freq 910e6 --rx-gain 50 --tx-gain 60 --ampl 0.5
```

Press Ctrl+C to stop and print results.

## Known Issues

- **B210 TX underruns**: The feedback loop (reader → gate) generates TX
  samples on-the-fly. The B210's USB transport introduces latency that causes
  TX underruns (`U` warnings), corrupting query waveforms. The N210's
  Ethernet transport handles this better. A fix would pre-buffer query
  waveforms instead of generating them sample-by-sample.
- **Offline test CRC**: The included test recording has marginal signal
  quality — the pipeline decodes RN16 and EPC bits but CRC-16 fails. This is
  a signal quality issue, not a code bug.
- **B210 USB firmware**: The B210 sometimes fails to load FX3 firmware on
  connect (stays at VID `2500` PID `0020`). Power-cycling the USB port via
  sysfs `authorized` attribute resolves this:
  ```bash
  echo 0 | sudo tee /sys/bus/usb/devices/<port>/authorized
  sleep 5
  echo 1 | sudo tee /sys/bus/usb/devices/<port>/authorized
  ```

## Architecture

Three C++ blocks communicating via global singleton state:

- **gate** — pulse detection, gates tag responses based on Gen2 timing
- **tag_decoder** — FM0 differential decode, CRC-16 validation
- **reader** — Gen2 QUERY/ACK/QueryRep generation, inventory state machine

Flowgraph topology (feedback loop):
```
usrp_source → fir_filter(decim=5) → gate → tag_decoder → reader → amp → usrp_sink
                                                              ↑__________________|
```

## Original Authors

- Nikos Kargas (nkargas@isc.tuc.gr) — original Gen2-UHF-RFID-Reader
- Xin Liu — EMDCYY/gr-rfid fork (GR 3.8 updates, debug output)
