/******************************************************************************
 *
 * Copyright (c) 2019, the nbcelltest authors.
 *
 * This file is part of the nbcelltest library, distributed under the terms of
 * the Apache License 2.0.  The full license can be found in the LICENSE file.
 *
 */
import {JupyterFrontEnd} from "@jupyterlab/application";
import {IDocumentManager} from "@jupyterlab/docmanager";

export
const CELLTESTS_CATEGORY = "Celltests";

export
const CELLTESTS_TEST_ID = "celltests:test";

export
const CELLTESTS_LINT_ID = "celltests:lint";

export
const CELLTESTS_TEST_CAPTION = "Run Celltests";

export
const CELLTESTS_LINT_CAPTION = "Run Lint";

export
const CELLTEST_TOOL_CLASS = "CelltestTool";

export
const CELLTEST_TOOL_CONTROLS_CLASS = "CelltestsControls";

export
const CELLTEST_TOOL_RULES_CLASS = "CelltestsRules";

export
const CELLTEST_TOOL_EDITOR_CLASS = "CelltestsEditor";

export
const CELLTEST_RULES = [
  // TODO fetch from server
  {label: "Lines per Cell", key: "lines_per_cell", min: 1, step: 1, value: 10},
  {label: "Cells per Notebook", key: "cells_per_notebook", min: 1, step: 1, value: 20},
  {label: "Function definitions", key: "function_definitions", min: 0, step: 1, value: 10},
  {label: "Class definitions", key: "class_definitions", min: 0, step: 1, value: 5},
  {label: "Cell test coverage (%)", key: "cell_coverage", min: 1, max: 100, step: 1, value: 50}
];

export
function isEnabled(app: JupyterFrontEnd, docManager: IDocumentManager): () => boolean {
  return () => (app.shell.currentWidget &&
                docManager.contextForWidget(app.shell.currentWidget) &&
                docManager.contextForWidget(app.shell.currentWidget).model) ? true : false;
}
