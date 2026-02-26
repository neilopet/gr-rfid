/*
 * Copyright 2023 Xin Liu.
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#include <pybind11/complex.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace py = pybind11;

#include <gnuradio/rfid/tag_decoder.h>
#include <tag_decoder_pydoc.h>

void bind_tag_decoder(py::module& m)
{
    using tag_decoder = gr::rfid::tag_decoder;

    py::class_<tag_decoder, gr::block, gr::basic_block,
        std::shared_ptr<tag_decoder>>(m, "tag_decoder", D(tag_decoder))
        .def(py::init(&tag_decoder::make),
           py::arg("sample_rate"),
           D(tag_decoder, make))
        ;
}
