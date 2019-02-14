import {JupyterLab} from '@jupyterlab/application';
import {IDocumentManager} from '@jupyterlab/docmanager';

export
const CELLTESTS_CATEGORY = 'Celltests';

export 
const CELLTESTS_RUN_ID = 'celltests:newtest';

export
const CELLTESTS_RUN_CAPTION = 'Run Celltests';

export
const CELLTEST_TOOL_CLASS = 'CelltestTool';

export
const CELLTEST_TOOL_OPTIONS_CLASS = 'CelltestsOptions';

export
const CELLTEST_TOOL_EDITOR_CLASS = 'CelltestsEditor';

export
function isEnabled(app: JupyterLab, docManager: IDocumentManager): () => boolean {
    return () => { return (app.shell.currentWidget &&
                docManager.contextForWidget(app.shell.currentWidget) &&
                docManager.contextForWidget(app.shell.currentWidget).model) ? true: false;};
}