/******************************************************************************
 *
 * Copyright (c) 2019, the nbcelltest authors.
 *
 * This file is part of the nbcelltest library, distributed under the terms of
 * the Apache License 2.0.  The full license can be found in the LICENSE file.
 *
 */
/* eslint-disable max-classes-per-file */
/* eslint-disable id-blacklist */
import { BoxPanel, PanelLayout, Widget } from "@lumino/widgets";

import { Cell, CodeCellModel } from "@jupyterlab/cells";
import { CodeEditorWrapper} from "@jupyterlab/codeeditor";
import { editorServices } from "@jupyterlab/codemirror";
import { INotebookTracker } from "@jupyterlab/notebook";

import {CELLTEST_RULES,
  CELLTEST_TOOL_CONTROLS_CLASS,
  CELLTEST_TOOL_EDITOR_CLASS,
  CELLTEST_TOOL_RULES_CLASS} from "./utils";

/**
 * Widget responsible for holding test controls
 *
 * @class      ControlsWidget (name)
 */
class ControlsWidget extends BoxPanel {
  public constructor() {
    super({direction: "top-to-bottom"});

    /* Section Header */
    const label = document.createElement("label");
    label.textContent = "Tests";

    this.node.appendChild(label);
    this.node.classList.add(CELLTEST_TOOL_CONTROLS_CLASS);

    /* Add button */
    const div = document.createElement("div");
    const add = document.createElement("button");
    add.textContent = "Add";
    add.onclick = () => {
      this.add();
    };

    /* Save button */
    const save = document.createElement("button");
    save.textContent = "Save";
    save.onclick = () => {
      this.save();
    };

    /* Clear button */
    const clear = document.createElement("button");
    clear.textContent = "Clear";
    clear.onclick = () => {
      this.clear();
    };

    /* add to container */
    div.appendChild(add);
    div.appendChild(save);
    div.appendChild(clear);
    this.node.appendChild(div);
  }

  // eslint-disable-next-line @typescript-eslint/no-empty-function
  public add = () => {};
  // eslint-disable-next-line @typescript-eslint/no-empty-function
  public save = () => {};
  // eslint-disable-next-line @typescript-eslint/no-empty-function
  public clear = () => {};
}

/**
 * Widget responsible for holding test controls
 *
 * @class      ControlsWidget (name)
 */
class RulesWidget extends BoxPanel {

  public lines_per_cell: HTMLDivElement;
  public cells_per_notebook: HTMLDivElement;
  public function_definitions: HTMLDivElement;
  public class_definitions: HTMLDivElement;
  public cell_coverage: HTMLDivElement;

  public constructor() {
    super({direction: "top-to-bottom"});

    /* Section Header */
    const label = document.createElement("label");
    label.textContent = "Lint Rules";

    this.node.appendChild(label);
    this.node.classList.add(CELLTEST_TOOL_RULES_CLASS);

    /* Add button */
    const div = document.createElement("div");

    for (const val of [].slice.call(CELLTEST_RULES)) {
      const row = document.createElement("div");
      const span = document.createElement("span");
      span.textContent = val.label;

      const chkbx = document.createElement("input");
      chkbx.type = "checkbox";
      chkbx.name = val.key;

      const number = document.createElement("input");
      number.type = "number";
      number.name = val.key;

      chkbx.onchange = () => {
        number.disabled = !chkbx.checked;
        number.value = number.disabled ? "" : val.value;
        this.save();
      };

      number.onchange = () => {
        this.save();
      };

      if (val.min !== undefined) {
        number.min = val.min;
      }
      if (val.max !== undefined) {
        number.max = val.max;
      }
      if (val.step !== undefined) {
        number.step = val.step;
      }

      row.appendChild(span);
      row.appendChild(chkbx);
      row.appendChild(number);
      this.setByKey(val.key, row);
      div.appendChild(row);
    }
    this.node.appendChild(div);
  }

  public getByKey(key: string) {
    switch (key) {
    case "lines_per_cell": {return this.lines_per_cell; }
    case "cells_per_notebook": {return this.cells_per_notebook; }
    case "function_definitions": {return this.function_definitions; }
    case "class_definitions": {return this.class_definitions; }
    case "cell_coverage": {return this.cell_coverage; }
    }
  }

  public setByKey(key: string, elem: HTMLDivElement) {
    switch (key) {
    case "lines_per_cell": {this.lines_per_cell = elem; break; }
    case "cells_per_notebook": {this.cells_per_notebook = elem; break; }
    case "function_definitions": {this.function_definitions = elem; break; }
    case "class_definitions": {this.class_definitions = elem; break; }
    case "cell_coverage": {this.cell_coverage = elem; break; }
    }
  }

  public getValuesByKey(key: string) {
    let elem;
    switch (key) {
    case "lines_per_cell": {elem = this.lines_per_cell; break; }
    case "cells_per_notebook": {elem = this.cells_per_notebook; break; }
    case "function_definitions": {elem = this.function_definitions; break; }
    case "class_definitions": {elem = this.class_definitions; break; }
    case "cell_coverage": {elem = this.cell_coverage; break; }
    }
    const chkbx: HTMLInputElement = elem.querySelector('input[type="checkbox"]');
    const input: HTMLInputElement = elem.querySelector('input[type="number"]');
    return {key, enabled: chkbx.checked, value: Number(input.value)};
  }

  public setValuesByKey(key: string, checked= true, value: number = null) {
    let elem;
    switch (key) {
    case "lines_per_cell": {elem = this.lines_per_cell; break; }
    case "cells_per_notebook": {elem = this.cells_per_notebook; break; }
    case "function_definitions": {elem = this.function_definitions; break; }
    case "class_definitions": {elem = this.class_definitions; break; }
    case "cell_coverage": {elem = this.cell_coverage; break; }
    }
    const chkbx: HTMLInputElement = elem.querySelector('input[type="checkbox"]');
    const input: HTMLInputElement = elem.querySelector('input[type="number"]');
    if (input) {
      input.value = (value === null ? "" : String(value));
      input.disabled = !checked;
    }
    if (chkbx) {
      chkbx.checked = checked;
    }
  }

  // eslint-disable-next-line @typescript-eslint/no-empty-function
  public save = () => {};
}

/**
 * Widget holding the Celltests widget, container for options and editor
 *
 * @class      CelltestsWidget (name)
 */
export class CelltestsWidget extends Widget {
  public currentActiveCell: Cell = null;
  public notebookTracker: INotebookTracker = null;
  private editor: CodeEditorWrapper = null;
  private rules: RulesWidget;

  public constructor() {
    super();

    /* create layout */
    const layout = (this.layout = new PanelLayout());

    /* create options widget */
    const controls = new ControlsWidget();

    /* create options widget */
    const rules = (this.rules = new RulesWidget());

    /* create codemirror editor */
    // eslint-disable-next-line @typescript-eslint/unbound-method
    const editorOptions = { model: new CodeCellModel({}), factory: editorServices.factoryService.newInlineEditor };
    const editor = (this.editor = new CodeEditorWrapper(editorOptions));
    editor.addClass(CELLTEST_TOOL_EDITOR_CLASS);
    editor.model.mimeType = "text/x-ipython";

    /* add options and editor to widget */
    layout.addWidget(controls);
    layout.addWidget(editor);
    layout.addWidget(rules);

    /* set add button functionality */
    controls.add = () => {
      this.fetchAndSetTests(); return true;
    };
    /* set save button functionality */
    controls.save = () => {
      this.saveTestsForActiveCell(); return true;
    };
    /* set clear button functionality */
    controls.clear = () => {
      this.deleteTestsForActiveCell(); return true;
    };

    rules.save = () => {
      this.saveRulesForCurrentNotebook();
    };
  }

  public fetchAndSetTests(): void {
    const tests = [];
    const splits = this.editor.model.value.text.split(/\n/);
    // eslint-disable-next-line @typescript-eslint/prefer-for-of
    for (let i = 0; i < splits.length; i++) {
      tests.push(splits[i] + "\n");
    }
    if (this.currentActiveCell !== null && this.currentActiveCell.model.type === "code") {
      this.currentActiveCell.model.metadata.set("celltests", tests);
    }
  }

  public loadTestsForActiveCell(): void {
    if (this.currentActiveCell !== null && this.currentActiveCell.model.type === "code") {
      let tests = this.currentActiveCell.model.metadata.get("celltests") as string[];
      let s = "";
      if (tests === undefined || tests.length === 0) {
        tests = ["# Use %cell to mark where the cell should be inserted, or add a line comment \"# no %cell\" to deliberately skip the cell\n", "%cell\n"];
      }
      // eslint-disable-next-line @typescript-eslint/prefer-for-of
      for (let i = 0; i < tests.length; i++) {
        s += tests[i];
      }
      this.editor.model.value.text = s;
      this.editor.editor.setOption("readOnly", false);

    } else {
      this.editor.model.value.text = "# Not a code cell";
      this.editor.editor.setOption("readOnly", true);
    }
  }

  public saveTestsForActiveCell(): void {
    /* if currentActiveCell exists */
    if (this.currentActiveCell !== null && this.currentActiveCell.model.type === "code") {
      const tests = [];
      const splits = this.editor.model.value.text.split(/\n/);
      // eslint-disable-next-line @typescript-eslint/prefer-for-of
      for (let i = 0; i < splits.length; i++) {
        tests.push(splits[i] + "\n");
      }
      this.currentActiveCell.model.metadata.set("celltests", tests);
    } else if (this.currentActiveCell !== null) {
      // TODO this?
      this.currentActiveCell.model.metadata.delete("celltests");
    }
  }

  public deleteTestsForActiveCell(): void {
    if (this.currentActiveCell !== null) {
      this.currentActiveCell.model.metadata.delete("celltests");
    }
  }

  public loadRulesForCurrentNotebook(): void {
    if (this.notebookTracker !== null) {
      const metadata: {[key: string]: number} = this.notebookTracker.currentWidget
        .model.metadata.get("celltests") as {[key: string]: number} || {};

      for (const rule of [].slice.call(CELLTEST_RULES)) {
        this.rules.setValuesByKey(rule.key, rule.key in metadata, metadata[rule.key]);
      }
    }
  }

  public saveRulesForCurrentNotebook(): void {
    if (this.notebookTracker !== null) {
      const metadata = {} as {[key: string]: number};

      for (const rule of [].slice.call(CELLTEST_RULES)) {
        const settings = this.rules.getValuesByKey(rule.key);
        if (settings.enabled) {
          metadata[settings.key] = settings.value;
        }
      }
      this.notebookTracker.currentWidget.model.metadata.set("celltests", metadata);
    }
  }

  public get editorWidget(): CodeEditorWrapper {
    return this.editor;
  }
}
