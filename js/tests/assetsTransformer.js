/******************************************************************************
 *
 * Copyright (c) 2019, the nbcelltests authors.
 *
 * This file is part of the nbcelltests library, distributed under the terms of
 * the Apache License 2.0.  The full license can be found in the LICENSE file.
 *
 */
const path = require("path");

module.exports = {
  process(src, filename, config, options) {
    return `module.exports = ${JSON.stringify(path.basename(filename))};`;
  },
};
