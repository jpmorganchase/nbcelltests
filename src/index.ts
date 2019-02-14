import {JupyterLabPlugin} from '@jupyterlab/application';
import {ICommandPalette} from '@jupyterlab/apputils';
import {IDocumentManager} from '@jupyterlab/docmanager';
import {ILauncher} from '@jupyterlab/launcher';
import {ICellTools, INotebookTracker} from "@jupyterlab/notebook";

import {activate} from './activate';
import '../style/index.css';


const extension: JupyterLabPlugin<void> = {
  id: 'jupyterlab_celltests',
  autoStart: true,
  requires: [IDocumentManager,
             ICommandPalette,
             INotebookTracker,
             ICellTools],
  optional: [ILauncher],
  activate: activate
};


export default extension;
export {activate as _activate};