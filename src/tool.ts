import { PanelLayout } from '@phosphor/widgets';
import { Message } from '@phosphor/messaging';

import { JupyterLab } from '@jupyterlab/application';
import { ICellTools, CellTools, INotebookTracker } from '@jupyterlab/notebook';
import { ObservableJSON } from '@jupyterlab/observables';

import { CELLTEST_TOOL_CLASS } from './utils';
import { CelltestsWidget } from './widget';


export class CelltestsTool extends CellTools.Tool {
  constructor(app: JupyterLab, notebook_Tracker: INotebookTracker, cellTools: ICellTools) {
    super();
    this.notebookTracker = notebook_Tracker;
    let layout = (this.layout = new PanelLayout());

    this.addClass(CELLTEST_TOOL_CLASS);
    this.widget = new CelltestsWidget();

    layout.addWidget(this.widget);
  }

  /**
   * Handle a change to the active cell.
   */
  protected onActiveCellChanged(msg: Message): void {
    this.widget.currentActiveCell = this.parent.activeCell;
    this.widget.loadTestsForActiveCell();
  }

  protected onAfterShow() {
    // this.widget.getAllTagsInNotebook();
  }

  protected onAfterAttach() {
    this.notebookTracker.currentWidget.context.ready.then(() => {
      // this.widget.getAllTagsInNotebook();
    });
    this.notebookTracker.currentChanged.connect(() => {
      // this.widget.getAllTagsInNotebook();
    });
    this.notebookTracker.currentWidget.model.cells.changed.connect(() => {
      // this.widget.getAllTagsInNotebook();
    });
  }

  protected onMetadataChanged(msg: ObservableJSON.ChangeMessage): void {
        this.widget.loadTestsForActiveCell();
  }

  private widget: CelltestsWidget = null;
  public notebookTracker: INotebookTracker = null;

}
