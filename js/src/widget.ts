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

import { CodeEditorWrapper, IEditorServices } from "@jupyterlab/codeeditor";

import circleSvg from "../style/circle.svg";
import { CELLTEST_RULES, CELLTEST_TOOL_CONTROLS_CLASS, CELLTEST_TOOL_EDITOR_CLASS, CELLTEST_TOOL_RULES_CLASS } from "./utils";
import { INotebookTracker } from "@jupyterlab/notebook";

const DEFAULT_TESTS = ['# Use %cell to mark where the cell should be inserted, or add a line comment "# no %cell" to deliberately skip the cell\n', "%cell\n"];

/**
 * Widget responsible for holding test controls
 *
 * @class      ControlsWidget (name)
 */
class ControlsWidget extends BoxPanel {
  label: HTMLLabelElement;

  svglabel: HTMLLabelElement;

  svg: HTMLElement;

  constructor() {
    super({ direction: "top-to-bottom" });

    /* Section Header */
    this.label = document.createElement("label");
    this.label.textContent = "Tests";

    this.svglabel = document.createElement("label");

    this.svg = document.createElement("svg");
    this.svg.innerHTML = circleSvg;
    this.svg = (this.svg.firstChild as HTMLElement);

    const div1 = document.createElement("div");
    div1.appendChild(this.label);

    const div2 = document.createElement("div");
    div1.appendChild(div2);

    div2.appendChild(this.svglabel);
    div2.appendChild(this.svg);

    this.node.appendChild(div1);
    this.node.classList.add(CELLTEST_TOOL_CONTROLS_CLASS);

    /* Add button */
    const div3 = document.createElement("div");
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
    div3.appendChild(add);
    div3.appendChild(save);
    div3.appendChild(clear);
    this.node.appendChild(div3);
  }

  // eslint-disable-next-line @typescript-eslint/no-empty-function
  add = () => {};

  // eslint-disable-next-line @typescript-eslint/no-empty-function
  save = () => {};

  // eslint-disable-next-line @typescript-eslint/no-empty-function
  clear = () => {};
}

/**
 * Widget responsible for holding test controls
 *
 * @class      ControlsWidget (name)
 */
class RulesWidget extends BoxPanel {
  label: HTMLLabelElement;
  lines_per_cell: HTMLDivElement;
  cells_per_notebook: HTMLDivElement;
  function_definitions: HTMLDivElement;
  class_definitions: HTMLDivElement;
  cell_coverage: HTMLDivElement;

  constructor() {
    super({ direction: "top-to-bottom" });

    /* Section Header */
    this.label = document.createElement("label");
    this.label.textContent = "Lint Rules";

    this.node.appendChild(this.label);
    this.node.classList.add(CELLTEST_TOOL_RULES_CLASS);

    /* Add button */
    const div = document.createElement("div");

    [].slice.call(CELLTEST_RULES).forEach((val: {[key: string]: string}) => {
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
    });
    this.node.appendChild(div);
  }

  getByKey(key: string) {
    switch (key) {
      case "lines_per_cell": {
        return this.lines_per_cell;
      }
      case "cells_per_notebook": {
        return this.cells_per_notebook;
      }
      case "function_definitions": {
        return this.function_definitions;
      }
      case "class_definitions": {
        return this.class_definitions;
      }
      case "cell_coverage": {
        return this.cell_coverage;
      }
      default:
        return undefined;
    }
  }

  setByKey(key: string, elem: HTMLDivElement) {
    switch (key) {
      case "lines_per_cell": {
        this.lines_per_cell = elem;
        break;
      }
      case "cells_per_notebook": {
        this.cells_per_notebook = elem;
        break;
      }
      case "function_definitions": {
        this.function_definitions = elem;
        break;
      }
      case "class_definitions": {
        this.class_definitions = elem;
        break;
      }
      case "cell_coverage": {
        this.cell_coverage = elem;
        break;
      }
      default:
    }
  }

  getValuesByKey(key: string) {
    let elem: HTMLDivElement;
    switch (key) {
      case "lines_per_cell": {
        elem = this.lines_per_cell;
        break;
      }
      case "cells_per_notebook": {
        elem = this.cells_per_notebook;
        break;
      }
      case "function_definitions": {
        elem = this.function_definitions;
        break;
      }
      case "class_definitions": {
        elem = this.class_definitions;
        break;
      }
      case "cell_coverage": {
        elem = this.cell_coverage;
        break;
      }
      default:
        return { key, enabled: false, value: 0 };
    }
    const chkbx = (elem.querySelector('input[type="checkbox"]') as HTMLInputElement);
    const input = (elem.querySelector('input[type="number"]') as HTMLInputElement);
    return { key, enabled: chkbx.checked, value: Number(input.value) };
  }

  setValuesByKey(key: string, checked = true, value: any = null) {
    let elem: HTMLDivElement;
    switch (key) {
      case "lines_per_cell": {
        elem = this.lines_per_cell;
        break;
      }
      case "cells_per_notebook": {
        elem = this.cells_per_notebook;
        break;
      }
      case "function_definitions": {
        elem = this.function_definitions;
        break;
      }
      case "class_definitions": {
        elem = this.class_definitions;
        break;
      }
      case "cell_coverage": {
        elem = this.cell_coverage;
        break;
      }
      default:
        return;
    }
    const chkbx = (elem.querySelector('input[type="checkbox"]') as HTMLInputElement);
    const input = (elem.querySelector('input[type="number"]') as HTMLInputElement);
    if (input) {
      input.value = value === null ? "" : String(value);
      input.disabled = !checked;
    }
    if (chkbx) {
      chkbx.checked = checked;
    }
  }

  // eslint-disable-next-line @typescript-eslint/no-empty-function
  save = () => {};
}

/**
 * Widget holding the Celltests widget, container for options and editor
 *
 * @class      CelltestsWidget (name)
 */
export class CelltestsWidget extends Widget {
  currentActiveCell: Cell;
  notebookTracker: INotebookTracker;
  editor: CodeEditorWrapper;
  rules: RulesWidget;
  controls: ControlsWidget;

  constructor(editorServices: IEditorServices) {
    super();

    /* create layout */
    this.layout = new PanelLayout();

    /* create options widget */
    this.controls = new ControlsWidget();

    /* create options widget */
    this.rules = new RulesWidget();

    /* create codemirror editor */
    const editorOptions = {
      factory: editorServices.factoryService.newInlineEditor,
      model: new CodeCellModel({}),
    };
    this.editor = new CodeEditorWrapper(editorOptions);
    this.editor.addClass(CELLTEST_TOOL_EDITOR_CLASS);
    this.editor.model.mimeType = "text/x-ipython";

    /* add options and editor to widget */
    (this.layout as PanelLayout).addWidget(this.controls);
    (this.layout as PanelLayout).addWidget(this.editor);
    (this.layout as PanelLayout).addWidget(this.rules);

    /* set add button functionality */
    this.controls.add = () => {
      this.fetchAndSetTests();
      return true;
    };
    /* set save button functionality */
    this.controls.save = () => {
      this.saveTestsForActiveCell();
      return true;
    };
    /* set clear button functionality */
    this.controls.clear = () => {
      this.deleteTestsForActiveCell();
      return true;
    };

    this.rules.save = () => {
      this.saveRulesForCurrentNotebook();
    };

    this.fetchAndSetTests.bind(this);
    this.loadTestsForActiveCell.bind(this);
    this.saveTestsForActiveCell.bind(this);
    this.deleteTestsForActiveCell.bind(this);
    this.loadRulesForCurrentNotebook.bind(this);
    this.setIndicatorNoTests.bind(this);
    this.setIndicatorTests.bind(this);
    this.setIndicatorNonCode.bind(this);
  }

  fetchAndSetTests() {
    const tests: string[] = [];
    const splits = this.editor.model.sharedModel.source.split(/\n/);
    splits.forEach(split => {
      tests.push(`${split}\n`);
    });
    if (this.currentActiveCell !== null && this.currentActiveCell.model.type === "code") {
      this.currentActiveCell.model.setMetadata("celltests", tests);
      this.setIndicatorTests();
    }
  }

  loadTestsForActiveCell() {
    if (this.currentActiveCell !== null && this.currentActiveCell.model.type === "code") {
      let tests = this.currentActiveCell.model.getMetadata("tests");
      if (tests === undefined || tests.length === 0) {
        tests = DEFAULT_TESTS;
        this.setIndicatorNoTests();
      } else {
        this.setIndicatorTests();
      }

      this.editor.model.sharedModel.source = tests.join("");
      this.editor.editor.setOption("readOnly", false);
    } else {
      this.editor.model.sharedModel.source = "# Not a code cell";
      this.editor.editor.setOption("readOnly", true);
      this.setIndicatorNonCode();
    }
  }

  saveTestsForActiveCell() {
    /* if currentActiveCell exists */
    if (this.currentActiveCell !== null && this.currentActiveCell.model.type === "code") {
      const tests: string[] = [];
      const splits = this.editor.model.sharedModel.getSource().split(/\n/);
      splits.forEach(split => {
        tests.push(`${split}\n`);
      });
      this.currentActiveCell.model.setMetadata("tests", tests);
      this.setIndicatorTests();
    } else if (this.currentActiveCell !== null) {
      // TODO this?
      this.currentActiveCell.model.deleteMetadata("tests");
      this.setIndicatorNonCode();
    }
  }

  deleteTestsForActiveCell() {
    if (this.currentActiveCell !== null) {
      this.editor.model.sharedModel.source = "";
      this.currentActiveCell.model.deleteMetadata("tests");
      this.setIndicatorNoTests();
    }
  }

  loadRulesForCurrentNotebook() {
    if (this.notebookTracker !== null) {
      const metadata: {[key: string]: string} = this.notebookTracker.currentWidget?.model?.getMetadata("celltests") || {};

      [].slice.call(CELLTEST_RULES).forEach((rule: {[key: string]: string}) => {
        this.rules.setValuesByKey(rule.key, rule.key in metadata, metadata[rule.key]);
      });
    }
  }

  saveRulesForCurrentNotebook() {
    if (this.notebookTracker !== null) {
      const metadata: {[key: string]: number} = {};

      [].slice.call(CELLTEST_RULES).forEach((rule: {[key: string]: string}) => {
        const settings = this.rules.getValuesByKey(rule.key);
        if (settings.enabled) {
          metadata[settings.key] = settings.value;
        }
      });
      this.notebookTracker.currentWidget?.model?.setMetadata("celltests", metadata);
    }
  }

  get editorWidget() {
    return this.editor;
  }

  setIndicatorNoTests() {
    (this.controls.svg.firstElementChild?.firstElementChild as HTMLElement).style.fill = "#e75c57";
    this.controls.svglabel.textContent = "(No Tests)";
  }

  setIndicatorTests() {
    (this.controls.svg.firstElementChild?.firstElementChild as HTMLElement).style.fill = "#008000";
    this.controls.svglabel.textContent = "(Tests Exist)";
  }

  setIndicatorNonCode() {
    (this.controls.svg.firstElementChild?.firstElementChild as HTMLElement).style.fill = "var(--jp-inverse-layout-color3)";
    this.controls.svglabel.textContent = "(Non Code Cell)";
  }
}
