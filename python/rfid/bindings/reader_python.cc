/*
 * Copyright 2023 Xin Liu.
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#include <pybind11/complex.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace py = pybind11;

#include <gnuradio/rfid/reader.h>
#include <reader_pydoc.h>

void bind_reader(py::module& m)
{
    using reader = gr::rfid::reader;

    py::class_<reader, gr::block, gr::basic_block,
        std::shared_ptr<reader>>(m, "reader", D(reader))
        .def(py::init(&reader::make),
           py::arg("sample_rate"),
           py::arg("dac_rate"),
           D(reader, make))
        .def("print_results", &reader::print_results,
           D(reader, print_results))
        ;
}
