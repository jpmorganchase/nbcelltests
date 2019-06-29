import {JupyterFrontEnd} from "@jupyterlab/application";
import {ICommandPalette} from "@jupyterlab/apputils";
import {IDocumentManager} from "@jupyterlab/docmanager";
import {INotebookTools, INotebookTracker} from "@jupyterlab/notebook";

import {runCellLints, runCellTests} from "./run";
import {CelltestsTool} from "./tool";
// tslint:disable-next-line:max-line-length
import {CELLTESTS_CATEGORY, CELLTESTS_LINT_CAPTION, CELLTESTS_LINT_ID, CELLTESTS_TEST_CAPTION, CELLTESTS_TEST_ID, isEnabled} from "./utils";

export
function activate(app: JupyterFrontEnd,
                  docManager: IDocumentManager,
                  palette: ICommandPalette,
                  tracker: INotebookTracker,
                  cellTools: INotebookTools): void {

    /* Add to cell tools sidebar */
    const testsTool = new CelltestsTool(app, tracker, cellTools);
    cellTools.addItem({ tool: testsTool, rank: 1.9 });

    /* Add to commands to sidebar */
    palette.addItem({command: CELLTESTS_TEST_ID, category: CELLTESTS_CATEGORY});
    palette.addItem({command: CELLTESTS_LINT_ID, category: CELLTESTS_CATEGORY});

    app.commands.addCommand(CELLTESTS_TEST_ID, {
        caption: CELLTESTS_TEST_CAPTION,
        execute: (args) => {
            runCellTests(app, docManager);
        },
        isEnabled: isEnabled(app, docManager),
        label: CELLTESTS_TEST_CAPTION,
    });

    app.commands.addCommand(CELLTESTS_LINT_ID, {
        caption: CELLTESTS_LINT_CAPTION,
        execute: (args) => {
            runCellLints(app, docManager);
        },
        isEnabled: isEnabled(app, docManager),
        label: CELLTESTS_LINT_CAPTION,
    });
}
