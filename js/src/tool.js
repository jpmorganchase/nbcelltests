/******************************************************************************
 *
 * Copyright (c) 2019, the nbcelltest authors.
 *
 * This file is part of the nbcelltest library, distributed under the terms of
 * the Apache License 2.0.  The full license can be found in the LICENSE file.
 *
 */
import {PanelLayout, Widget} from "@lumino/widgets";

import {NotebookTools} from "@jupyterlab/notebook";

import {CELLTEST_TOOL_CLASS} from "./utils";
import {CelltestsWidget} from "./widget";

export class CelltestsTool extends NotebookTools.Tool {
  notebookTracker = null;

  cellTools = null;

  widget = null;

  constructor(app, notebook_Tracker, cellTools, editorServices) {
    super();
    this.notebookTracker = notebook_Tracker;
    this.cellTools = cellTools;
    this.layout = new PanelLayout();

    /* Section Header */
    const label = document.createElement("label");
    label.textContent = "Celltests";
    this.layout.addWidget(new Widget({node: label}));

    this.addClass(CELLTEST_TOOL_CLASS);
    this.widget = new CelltestsWidget(editorServices);
    this.widget.notebookTracker = notebook_Tracker;

    this.layout.addWidget(this.widget);
  }

  /**
   * Handle a change to the active cell.
   */
  onActiveCellChanged(msg) {
    this.widget.currentActiveCell = this.cellTools.activeCell;
    this.widget.loadTestsForActiveCell();
  }

  onAfterShow() {}

  onAfterAttach() {
    if (this.notebookTracker.currentWidget === null) {
      return;
    }

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

  onMetadataChanged(msg) {
    this.widget.loadTestsForActiveCell();
    this.widget.loadRulesForCurrentNotebook();
  }
}
