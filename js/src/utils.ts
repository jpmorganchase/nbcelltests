import { JupyterFrontEnd } from "@jupyterlab/application";
import { IDocumentManager } from "@jupyterlab/docmanager";

/******************************************************************************
 *
 * Copyright (c) 2019, the nbcelltest authors.
 *
 * This file is part of the nbcelltest library, distributed under the terms of
 * the Apache License 2.0.  The full license can be found in the LICENSE file.
 *
 */
export const CELLTESTS_ID = "nbcelltests";

export const CELLTESTS_CATEGORY = "Cell Tests";

export const CELLTESTS_TEST_ID = "nbcelltests:test";

export const CELLTESTS_LINT_ID = "nbcelltests:lint";

export const CELLTESTS_TEST_CAPTION = "Run Celltests";

export const CELLTESTS_LINT_CAPTION = "Run Lint";

export const CELLTEST_TOOL_CLASS = "CelltestTool";

export const CELLTEST_TOOL_CONTROLS_CLASS = "CelltestsControls";

export const CELLTEST_TOOL_RULES_CLASS = "CelltestsRules";

export const CELLTEST_TOOL_EDITOR_CLASS = "CelltestsEditor";

export const CELLTEST_RULES = [
  // TODO fetch from server
  {
    key: "lines_per_cell",
    label: "Lines per Cell",
    min: 1,
    step: 1,
    value: 10,
  },
  {
    key: "cells_per_notebook",
    label: "Cells per Notebook",
    min: 1,
    step: 1,
    value: 20,
  },
  {
    key: "function_definitions",
    label: "Function definitions",
    min: 0,
    step: 1,
    value: 10,
  },
  {
    key: "class_definitions",
    label: "Class definitions",
    min: 0,
    step: 1,
    value: 5,
  },
  {
    key: "cell_coverage",
    label: "Cell test coverage (%)",
    max: 100,
    min: 1,
    step: 1,
    value: 50,
  },
];

export function isEnabled(app: JupyterFrontEnd, docManager: IDocumentManager) {
  return () => !!(app.shell.currentWidget && docManager.contextForWidget(app.shell.currentWidget) && docManager.contextForWidget(app.shell.currentWidget)?.model);
}
