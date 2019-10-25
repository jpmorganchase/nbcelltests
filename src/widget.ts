import { BoxPanel, PanelLayout, Widget } from "@phosphor/widgets";

import { Cell, CodeCellModel } from "@jupyterlab/cells";
import { CodeEditorWrapper} from "@jupyterlab/codeeditor";
import { editorServices } from "@jupyterlab/codemirror";
import { INotebookTracker } from "@jupyterlab/notebook";

import {CELLTEST_TOOL_CLASS,
        CELLTEST_TOOL_CONTROLS_CLASS,
        CELLTEST_TOOL_EDITOR_CLASS,
        CELLTEST_TOOL_RULES_CLASS} from "./utils";

/**
 * Widget responsible for holding test controls
 *
 * @class      ControlsWidget (name)
 */
class ControlsWidget extends BoxPanel {
    constructor() {
        super({direction: "top-to-bottom"});

        /* Section Header */
        const label = document.createElement("label");
        label.textContent = "Celltests";

        this.node.appendChild(label);
        this.node.classList.add(CELLTEST_TOOL_CONTROLS_CLASS);

        /* Add button */
        const div = document.createElement("div");
        const add = document.createElement("button");
        add.textContent = "Add";
        add.onclick = () => { this.add(); };

        /* Save button */
        const save = document.createElement("button");
        save.textContent = "Save";
        save.onclick = () => { this.save(); };

        /* Clear button */
        const clear = document.createElement("button");
        clear.textContent = "Clear";
        clear.onclick = () => {this.clear(); };

        /* add to container */
        div.appendChild(add);
        div.appendChild(save);
        div.appendChild(clear);
        this.node.appendChild(div);
    }

    // tslint:disable-next-line:no-empty
    public add = () => {};
    // tslint:disable-next-line:no-empty
    public save = () => {};
    // tslint:disable-next-line:no-empty
    public clear = () => {};
}

/**
 * Widget responsible for holding test controls
 *
 * @class      ControlsWidget (name)
 */
// tslint:disable-next-line:max-classes-per-file
class RulesWidget extends BoxPanel {

    // tslint:disable-next-line:variable-name
    public lines_per_cell: HTMLDivElement;
    // tslint:disable-next-line:variable-name
    public cells_per_notebook: HTMLDivElement;
    // tslint:disable-next-line:variable-name
    public function_definitions: HTMLDivElement;
    // tslint:disable-next-line:variable-name
    public class_definitions: HTMLDivElement;
    // tslint:disable-next-line:variable-name
    public cell_coverage: HTMLDivElement;

    constructor() {
        super({direction: "top-to-bottom"});

        /* Section Header */
        const label = document.createElement("label");
        label.textContent = "Celltests - Rules";

        this.node.appendChild(label);
        this.node.classList.add(CELLTEST_TOOL_RULES_CLASS);

        /* Add button */
        const div = document.createElement("div");

        const rules = [{label: "Lines per Cell", key: "lines_per_cell", min: 1, step: 1, value: 10},
                     {label: "Cells per Notebook", key: "cells_per_notebook", min: 1, step: 1, value: 20},
                     {label: "Function definitions", key: "function_definitions", min: 0, step: 1, value: 10},
                     {label: "Class definitions", key: "class_definitions", min: 0, step: 1, value: 5},
                     {label: "Cell test coverage (%)", key: "cell_coverage", min: 1, max: 100, step: 1, value: 50}];
        for (const val of [].slice.call(rules)) {
            const row = document.createElement("div");
            const span = document.createElement("span");
            span.textContent = val.label;

            const chkbx = document.createElement("input");
            chkbx.type = "checkbox";
            chkbx.name = val.key;

            // tslint:disable-next-line:variable-name
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

            if (val.min !== undefined) {number.min = val.min; }
            if (val.max !== undefined) {number.max = val.max; }
            if (val.step !== undefined) {number.step = val.step; }

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
        const chkbx = elem.querySelector('input[type="checkbox"]') as HTMLInputElement;
        const input = elem.querySelector('input[type="number"]') as HTMLInputElement;
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
        const chkbx = elem.querySelector('input[type="checkbox"]') as HTMLInputElement;
        const input = elem.querySelector('input[type="number"]') as HTMLInputElement;
        if (input) {
            input.value = (value === null ? "" : String(value));
            input.disabled = !checked;
        }
        if (chkbx) {chkbx.checked = checked; }
    }

    // tslint:disable-next-line:no-empty
    public save = () => {};
}

/**
 * Widget holding the Celltests widget, container for options and editor
 *
 * @class      CelltestsWidget (name)
 */
// tslint:disable-next-line:max-classes-per-file
export class CelltestsWidget extends Widget {
    public currentActiveCell: Cell = null;
    public notebookTracker: INotebookTracker = null;
    private editor: CodeEditorWrapper = null;
    private rules: RulesWidget;

    constructor() {
        super();
        this.node.classList.add(CELLTEST_TOOL_CLASS);

        /* create layout */
        const layout = (this.layout = new PanelLayout());

        /* create options widget */
        const controls = new ControlsWidget();

        /* create options widget */
        const rules = (this.rules = new RulesWidget());

        /* create codemirror editor */
        const editorOptions = { model: new CodeCellModel({}), factory: editorServices.factoryService.newInlineEditor };
        const editor = (this.editor = new CodeEditorWrapper(editorOptions));
        editor.addClass(CELLTEST_TOOL_EDITOR_CLASS);
        editor.model.mimeType = "text/x-ipython";

        /* add options and editor to widget */
        layout.addWidget(controls);
        layout.addWidget(editor);
        layout.addWidget(rules);

        /* set add button functionality */
        controls.add = () => {this.fetchAndSetTests(); return true; };
        /* set save button functionality */
        controls.save = () => { this.saveTestsForActiveCell(); return true; };
        /* set clear button functionality */
        controls.clear = () => {this.deleteTestsForActiveCell(); return true; };

        rules.save = () => {
            this.saveRulesForCurrentNotebook();
        };
    }

    public fetchAndSetTests(): void {
        const tests = [];
        const splits = this.editor.model.value.text.split(/\n/);
        // tslint:disable-next-line:prefer-for-of
        for (let i = 0; i < splits.length; i++) {
            tests.push(splits[i] + "\n");
        }
        this.currentActiveCell.model.metadata.set("tests", tests);
    }

    public loadTestsForActiveCell(): void {
        if (this.currentActiveCell !== null) {
            let tests = this.currentActiveCell.model.metadata.get("tests") as string[];
            let s = "";
            if (tests === undefined || tests.length === 0) {
                tests = ["# Use %cell to execute the cell\n"];
            }
            // tslint:disable-next-line:prefer-for-of
            for (let i = 0; i < tests.length; i++) {
                s += tests[i];
            }
            this.editor.model.value.text = s;

        } else {
            // tslint:disable-next-line:no-console
            console.warn("Celltests: Null cell warning");
        }
    }

    public saveTestsForActiveCell(): void {
        /* if currentActiveCell exists */
        if (this.currentActiveCell !== null) {
            const tests = [];
            const splits = this.editor.model.value.text.split(/\n/);
            // tslint:disable-next-line:prefer-for-of
            for (let i = 0; i < splits.length; i++) {
                tests.push(splits[i] + "\n");
            }
            this.currentActiveCell.model.metadata.set("tests", tests);
        } else {
            // tslint:disable-next-line:no-console
            console.warn("Celltests: Null cell warning");
        }
    }

    public deleteTestsForActiveCell(): void {
        if (this.currentActiveCell !== null) {
            this.currentActiveCell.model.metadata.delete("tests");
        } else {
            // tslint:disable-next-line:no-console
            console.warn("Celltests: Null cell warning");
        }
    }

    public loadRulesForCurrentNotebook(): void {
        if (this.notebookTracker !== null) {
            let metadata: {[key: string]: number};
            metadata = this.notebookTracker.currentWidget
                .model.metadata.get("celltests") as {[key: string]: number} || {};
            const rules = ["lines_per_cell",
                           "cells_per_notebook",
                           "function_definitions",
                           "class_definitions",
                           "cell_coverage"];
            for (const rule of [].slice.call(rules)) {
                this.rules.setValuesByKey(rule, rule in metadata, metadata[rule]);
            }
        } else {
            // tslint:disable-next-line:no-console
            console.warn("Celltests: Null notebook warning");
        }
    }

    public saveRulesForCurrentNotebook(): void {
        if (this.notebookTracker !== null) {
            const metadata = {} as {[key: string]: number};
            const rules = ["lines_per_cell",
                           "cells_per_notebook",
                           "function_definitions",
                           "class_definitions",
                           "cell_coverage"];
            for (const rule of [].slice.call(rules)) {
                const settings = this.rules.getValuesByKey(rule);
                if (settings.enabled) {
                    metadata[settings.key] = settings.value;
                }
            }
            this.notebookTracker.currentWidget.model.metadata.set("celltests", metadata);
        } else {
            // tslint:disable-next-line:no-console
            console.warn("Celltests: Null notebook warning");
        }
    }

    get editorWidget(): CodeEditorWrapper {
        return this.editor;
    }
}
