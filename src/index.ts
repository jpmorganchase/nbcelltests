import {JupyterLabPlugin} from "@jupyterlab/application";
import {ICommandPalette} from "@jupyterlab/apputils";
import {IDocumentManager} from "@jupyterlab/docmanager";
import {ILauncher} from "@jupyterlab/launcher";
import {ICellTools, INotebookTracker} from "@jupyterlab/notebook";

import "../style/index.css";
import {activate} from "./activate";

const extension: JupyterLabPlugin<void> = {
  activate,
  autoStart: true,
  id: "jupyterlab_celltests",
  optional: [ILauncher],
  requires: [IDocumentManager,
             ICommandPalette,
             INotebookTracker,
             ICellTools],
};

export default extension;
export {activate as _activate};
