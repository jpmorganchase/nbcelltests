import { Message } from "@phosphor/messaging";
import { PanelLayout } from "@phosphor/widgets";

import { JupyterFrontEnd } from "@jupyterlab/application";
import { INotebookTools, INotebookTracker, NotebookTools } from "@jupyterlab/notebook";
import { ObservableJSON } from "@jupyterlab/observables";

import { CELLTEST_TOOL_CLASS } from "./utils";
import { CelltestsWidget } from "./widget";

export class CelltestsTool extends NotebookTools.Tool {
  public notebookTracker: INotebookTracker = null;
  public cellTools: INotebookTools = null;

  private widget: CelltestsWidget = null;
  // tslint:disable-next-line:variable-name
  constructor(app: JupyterFrontEnd, notebook_Tracker: INotebookTracker, cellTools: INotebookTools) {
    super();
    this.notebookTracker = notebook_Tracker;
    this.cellTools = cellTools;
    const layout = (this.layout = new PanelLayout());

    this.addClass(CELLTEST_TOOL_CLASS);
    this.widget = new CelltestsWidget();
    this.widget.notebookTracker = notebook_Tracker;

    layout.addWidget(this.widget);
  }

  /**
   * Handle a change to the active cell.
   */
  protected onActiveCellChanged(msg: Message): void {
    this.widget.currentActiveCell = this.cellTools.activeCell;
    this.widget.loadTestsForActiveCell();
  }

  // tslint:disable-next-line:no-empty
  protected onAfterShow() {

  }

  protected onAfterAttach() {
    this.notebookTracker.currentWidget.context.ready.then(() => {
      this.widget.loadTestsForActiveCell();
      this.widget.loadRulesForCurrentNotebook();
    });
    this.notebookTracker.currentChanged.connect(() => {
      this.widget.loadTestsForActiveCell();
      this.widget.loadRulesForCurrentNotebook();
    });
    this.notebookTracker.currentWidget.model.cells.changed.connect(() => {
      this.widget.loadTestsForActiveCell();
      this.widget.loadRulesForCurrentNotebook();
    });
  }

  protected onMetadataChanged(msg: ObservableJSON.ChangeMessage): void {
    this.widget.loadTestsForActiveCell();
    this.widget.loadRulesForCurrentNotebook();
  }

}
