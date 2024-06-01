/******************************************************************************
 *
 * Copyright (c) 2019, the nbcelltest authors.
 *
 * This file is part of the nbcelltest library, distributed under the terms of
 * the Apache License 2.0.  The full license can be found in the LICENSE file.
 *
 */
import {ICommandPalette} from "@jupyterlab/apputils";
import {IDocumentManager} from "@jupyterlab/docmanager";
import {ILauncher} from "@jupyterlab/launcher";
import {INotebookTools, INotebookTracker} from "@jupyterlab/notebook";
import {IEditorServices} from "@jupyterlab/codeeditor";

import "../style/index.css";
import {activate} from "./activate";
import {CELLTESTS_ID} from "./utils";

const extension = {
  activate,
  autoStart: true,
  id: CELLTESTS_ID,
  optional: [ILauncher],
  requires: [IDocumentManager, ICommandPalette, INotebookTracker, INotebookTools, IEditorServices],
};

export default extension;
export {activate as _activate};
