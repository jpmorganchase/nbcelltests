import {JupyterLab} from '@jupyterlab/application';
import {ICommandPalette} from '@jupyterlab/apputils';
import {IDocumentManager} from '@jupyterlab/docmanager';
import {ICellTools, INotebookTracker} from "@jupyterlab/notebook";

import {CelltestsTool} from './tool';
import {runCellTests} from './run';
import {isEnabled, CELLTESTS_RUN_CAPTION, CELLTESTS_RUN_ID, CELLTESTS_CATEGORY} from './utils';

export
function activate(app: JupyterLab,
    docManager: IDocumentManager,
    palette: ICommandPalette,
    tracker: INotebookTracker,
    cellTools: ICellTools): void {

    /* Add to cell tools sidebar */
    let testsTool = new CelltestsTool(app, tracker, cellTools);
    cellTools.addItem({ tool: testsTool, rank: 1.9 });



    /* Add to commands to sidebar */
    palette.addItem({command: CELLTESTS_RUN_ID, category: CELLTESTS_CATEGORY});

    app.commands.addCommand(CELLTESTS_RUN_ID, {
        label: CELLTESTS_RUN_CAPTION,
        execute: args => {
            runCellTests(app, docManager);
        },
        isEnabled: isEnabled(app, docManager),
        caption: CELLTESTS_RUN_CAPTION,
        iconClass: 'fa fa-sign-out jp-IconTest'
    });
}
