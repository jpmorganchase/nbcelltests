import {JupyterLab} from '@jupyterlab/application';
import {ICommandPalette} from '@jupyterlab/apputils';
import {IDocumentManager} from '@jupyterlab/docmanager';
import {ICellTools, INotebookTracker} from "@jupyterlab/notebook";

import {CelltestsTool} from './tool';
import {runCellTests, runCellLints} from './run';
import {isEnabled, CELLTESTS_TEST_CAPTION, CELLTESTS_LINT_CAPTION, CELLTESTS_TEST_ID, CELLTESTS_LINT_ID, CELLTESTS_CATEGORY} from './utils';

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
    palette.addItem({command: CELLTESTS_TEST_ID, category: CELLTESTS_CATEGORY});
    palette.addItem({command: CELLTESTS_LINT_ID, category: CELLTESTS_CATEGORY});

    app.commands.addCommand(CELLTESTS_TEST_ID, {
        label: CELLTESTS_TEST_CAPTION,
        execute: args => {
            runCellTests(app, docManager);
        },
        isEnabled: isEnabled(app, docManager),
        caption: CELLTESTS_TEST_CAPTION
    });

    app.commands.addCommand(CELLTESTS_LINT_ID, {
        label: CELLTESTS_LINT_CAPTION,
        execute: args => {
            runCellLints(app, docManager);
        },
        isEnabled: isEnabled(app, docManager),
        caption: CELLTESTS_LINT_CAPTION
    });
}
