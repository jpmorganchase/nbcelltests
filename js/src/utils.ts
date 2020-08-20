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
const CELLTESTS_CATEGORY = "NBCelltests";

export
const CELLTESTS_TEST_ID = "nbcelltests:test";

export
const CELLTESTS_LINT_ID = "nbcelltests:lint";

export
const CELLTESTS_TEST_CAPTION = "Run Celltests";

export
const CELLTESTS_LINT_CAPTION = "Run Lint";

export
const CELLTEST_TOOL_CLASS = "NBCelltestTool";

export
const CELLTEST_TOOL_CONTROLS_CLASS = "NBCelltestsControls";

export
const CELLTEST_TOOL_RULES_CLASS = "NBCelltestsRules";

export
const CELLTEST_TOOL_EDITOR_CLASS = "NBCelltestsEditor";

export
function isEnabled(app: JupyterFrontEnd, docManager: IDocumentManager): () => boolean {
  return () => (app.shell.currentWidget &&
                docManager.contextForWidget(app.shell.currentWidget) &&
                docManager.contextForWidget(app.shell.currentWidget).model) ? true : false;
}
