/*
 * Copyright 2023 Xin Liu.
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#include <pybind11/complex.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace py = pybind11;

#include <gnuradio/rfid/gate.h>
#include <gate_pydoc.h>

void bind_gate(py::module& m)
{
    using gate = gr::rfid::gate;

    py::class_<gate, gr::block, gr::basic_block,
        std::shared_ptr<gate>>(m, "gate", D(gate))
        .def(py::init(&gate::make),
           py::arg("sample_rate"),
           D(gate, make))
        ;
}
