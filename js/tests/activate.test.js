/******************************************************************************
 *
 * Copyright (c) 2019, the nbcelltests authors.
 *
 * This file is part of the nbcelltests library, distributed under the terms of
 * the Apache License 2.0.  The full license can be found in the LICENSE file.
 *
 */
import "isomorphic-fetch";

import {_activate} from "../src/index";

describe("Checks activate", () => {
  test("Check activate", () => {
    expect(_activate);
  });
});
