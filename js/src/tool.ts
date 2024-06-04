/******************************************************************************
 *
 * Copyright (c) 2019, the nbcelltest authors.
 *
 * This file is part of the nbcelltest library, distributed under the terms of
 * the Apache License 2.0.  The full license can be found in the LICENSE file.
 *
 */
import { PanelLayout, Widget } from "@lumino/widgets";

import { INotebookTools, INotebookTracker, NotebookTools } from "@jupyterlab/notebook";
import { ObservableJSON } from "@jupyterlab/observables";

import { CELLTEST_TOOL_CLASS } from "./utils";
import { CelltestsWidget } from "./widget";
import { JupyterFrontEnd } from "@jupyterlab/application";
import { IEditorServices } from "@jupyterlab/codeeditor";

export class CelltestsTool extends NotebookTools.Tool {
  notebookTracker: INotebookTracker;

  cellTools: INotebookTools;

  private widget: CelltestsWidget;

  constructor(app: JupyterFrontEnd, notebook_Tracker: INotebookTracker, cellTools: INotebookTools, editorServices: IEditorServices) {
    super();
    this.notebookTracker = notebook_Tracker;
    this.cellTools = cellTools;
    this.layout = new PanelLayout();

    /* Section Header */
    const label = document.createElement("label");
    label.textContent = "Celltests";
    (this.layout as PanelLayout).addWidget(new Widget({ node: label }));

    this.addClass(CELLTEST_TOOL_CLASS);
    this.widget = new CelltestsWidget(editorServices);
    this.widget.notebookTracker = notebook_Tracker;

    (this.layout as PanelLayout).addWidget(this.widget);
  }

  /**
   * Handle a change to the active cell.
   */
  protected onActiveCellChanged() {
    if (this.cellTools.activeCell) {
      this.widget.currentActiveCell = this.cellTools.activeCell;
      this.widget.loadTestsForActiveCell();
    }
  }

  // eslint-disable-next-line @typescript-eslint/no-empty-function
  protected onAfterShow() {}

  protected onAfterAttach() {
    if (this.notebookTracker.currentWidget === null) {
      return;
    }

    void this.notebookTracker.currentWidget.context.ready.then(() => {
      this.widget.loadTestsForActiveCell();
      this.widget.loadRulesForCurrentNotebook();
    });
    this.notebookTracker.currentChanged.connect(() => {
      this.widget.loadTestsForActiveCell();
      this.widget.loadRulesForCurrentNotebook();
    });
    this.notebookTracker.currentWidget.model?.cells.changed.connect(() => {
      this.widget.loadTestsForActiveCell();
      this.widget.loadRulesForCurrentNotebook();
    });
  }

  protected onMetadataChanged(msg: ObservableJSON.ChangeMessage): void {
    this.widget.loadTestsForActiveCell();
    this.widget.loadRulesForCurrentNotebook();
  }
}
