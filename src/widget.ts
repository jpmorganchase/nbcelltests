import { Widget, PanelLayout, BoxPanel } from '@phosphor/widgets';

import { Cell, CodeCellModel } from '@jupyterlab/cells';
import { editorServices } from '@jupyterlab/codemirror';
import { CodeEditorWrapper} from '@jupyterlab/codeeditor';
import { INotebookTracker } from '@jupyterlab/notebook';

import {CELLTEST_TOOL_CLASS, CELLTEST_TOOL_CONTROLS_CLASS, CELLTEST_TOOL_RULES_CLASS, CELLTEST_TOOL_EDITOR_CLASS} from './utils';

/**
 * Widget responsible for holding test controls
 *
 * @class      ControlsWidget (name)
 */
class ControlsWidget extends BoxPanel {
    constructor() {
        super({direction: 'top-to-bottom'});

        /* Section Header */
        let label = document.createElement('label')
        label.textContent = 'Celltests';

        this.node.appendChild(label);
        this.node.classList.add(CELLTEST_TOOL_CONTROLS_CLASS);

        /* Add button */
        let div = document.createElement('div');
        let add = document.createElement('button');
        add.textContent = 'Add';
        add.onclick = () => { this.add();}

        /* Save button */
        let save = document.createElement('button');
        save.textContent = 'Save';
        save.onclick = () => { this.save();}

        /* Clear button */
        let clear = document.createElement('button');
        clear.textContent = 'Clear';
        clear.onclick = () => {this.clear();}

        /* add to container */
        div.appendChild(add);
        div.appendChild(save);
        div.appendChild(clear);
        this.node.appendChild(div);
    }

    add = ()=>{};
    save = ()=>{};
    clear = ()=>{};
}

/**
 * Widget responsible for holding test controls
 *
 * @class      ControlsWidget (name)
 */
class RulesWidget extends BoxPanel {
    constructor() {
        super({direction: 'top-to-bottom'});

        /* Section Header */
        let label = document.createElement('label')
        label.textContent = 'Celltests - Rules';

        this.node.appendChild(label);
        this.node.classList.add(CELLTEST_TOOL_RULES_CLASS);

        /* Add button */
        let div = document.createElement('div');

        let rules = [{label: 'Lines per Cell', key: 'lines_per_cell', min: 1, step: 1, value:0},
                     {label: 'Cells per Notebook', key: 'cells_per_notebook', min: 1, step: 1, value:0},
                     {label: 'Function definitions', key: 'function_definitions', min: 1, step: 1, value:0},
                     {label: 'Class definitions', key: 'class_definitions', min: 1, step: 1, value:0},
                     {label: 'Cell test coverage (%)', key: 'cell_coverage', min: 1, max:100, step: 1, value:0}];
        for(let val of [].slice.call(rules)){
            let row = document.createElement('div');
            let span = document.createElement('span');
            span.textContent = val.label;

            let chkbx = document.createElement('input');
            chkbx.type = 'checkbox';
            chkbx.name = val.key;

            let number = document.createElement('input');
            number.type = 'number';
            number.name = val.key;

            chkbx.onchange = () => {
                if(chkbx.checked){
                    number.disabled = false;
                    this.save();
                } else {
                    number.disabled = true;
                    this.save();
                }
            }

            if(val.min){number.min = val.min;}
            if(val.max){number.max = val.max;}
            if(val.step){number.step = val.step;}

            row.appendChild(span);
            row.appendChild(chkbx);
            row.appendChild(number);
            this.setByKey(val.key, row);
            div.appendChild(row);
        }
        this.node.appendChild(div);
    }

    getByKey(key: string){
        switch(key){
            case 'lines_per_cell': {return this.lines_per_cell;}
            case 'cells_per_notebook': {return this.cells_per_notebook;}
            case 'function_definitions': {return this.function_definitions;}
            case 'class_definitions': {return this.class_definitions;}
            case 'cell_coverage': {return this.cell_coverage;}
        }
    }

    setByKey(key: string, elem: HTMLDivElement){
        switch(key){
            case 'lines_per_cell': {this.lines_per_cell = elem; break;}
            case 'cells_per_notebook': {this.cells_per_notebook = elem; break;}
            case 'function_definitions': {this.function_definitions = elem; break;}
            case 'class_definitions': {this.class_definitions = elem; break;}
            case 'cell_coverage': {this.cell_coverage = elem; break;}
        }
    }

    getValuesByKey(key: string){
        let elem;
        switch(key){
            case 'lines_per_cell': {elem = this.lines_per_cell; break;}
            case 'cells_per_notebook': {elem =this.cells_per_notebook; break;}
            case 'function_definitions': {elem = this.function_definitions; break;}
            case 'class_definitions': {elem = this.class_definitions; break;}
            case 'cell_coverage': {elem = this.cell_coverage; break;}
        }
        let chkbx = elem.querySelector('input[type="checkbox"]') as HTMLInputElement;
        let input = elem.querySelector('input[type="number"]') as HTMLInputElement;
        return {key: key, enabled:chkbx.checked, value:input.value};
    }

    setValuesByKey(key: string, checked=true, value: string|number = 0){
        let elem;
        switch(key){
            case 'lines_per_cell': {elem = this.lines_per_cell; break;}
            case 'cells_per_notebook': {elem =this.cells_per_notebook; break;}
            case 'function_definitions': {elem = this.function_definitions; break;}
            case 'class_definitions': {elem = this.class_definitions; break;}
            case 'cell_coverage': {elem = this.cell_coverage; break;}
        }
        let chkbx = elem.querySelector('input[type="checkbox"]') as HTMLInputElement;
        let input = elem.querySelector('input[type="number"]') as HTMLInputElement;
        if(input){input.value = value.toString();}
        if(chkbx){chkbx.checked = checked;}
    }


    lines_per_cell: HTMLDivElement;
    cells_per_notebook: HTMLDivElement;
    function_definitions: HTMLDivElement;
    class_definitions: HTMLDivElement;
    cell_coverage: HTMLDivElement;

    save = ()=>{};
}


/**
 * Widget holding the Celltests widget, container for options and editor
 *
 * @class      CelltestsWidget (name)
 */
export class CelltestsWidget extends Widget {
    constructor() {
        super()
        this.node.classList.add(CELLTEST_TOOL_CLASS);

        /* create layout */
        let layout = (this.layout = new PanelLayout());

        /* create options widget */
        let controls = new ControlsWidget();

        /* create options widget */
        let rules = (this.rules = new RulesWidget());

        /* create codemirror editor */
        let editorOptions = { model: new CodeCellModel({}), factory: editorServices.factoryService.newInlineEditor };
        let editor = (this.editor = new CodeEditorWrapper(editorOptions));
        editor.addClass(CELLTEST_TOOL_EDITOR_CLASS);
        editor.model.mimeType = 'text/x-ipython';

        /* add options and editor to widget */
        layout.addWidget(controls);
        layout.addWidget(editor);
        layout.addWidget(rules);

        /* set add button functionality */
        controls.add = () => {this.fetchAndSetTests(); return true;}
        /* set save button functionality */
        controls.save = () => { this.saveTestsForActiveCell(); return true;}
        /* set clear button functionality */
        controls.clear = () => {this.deleteTestsForActiveCell(); return true;};

        rules.save = () => {
            this.saveRulesForCurrentNotebook();
        };
    }


    fetchAndSetTests(): void {
        let tests = [];
        let splits = this.editor.model.value.text.split(/\n/);
        for(let i=0; i<splits.length; i++){
            tests.push(splits[i] + '\n');
        }
        this.currentActiveCell.model.metadata.set('tests', tests);
    }

    loadTestsForActiveCell(): void {
        if (this.currentActiveCell !== null) {
            let tests = this.currentActiveCell.model.metadata.get('tests') as Array<string>;
            let s = '';
            if(tests === undefined || tests.length === 0){
                tests = ['# Use %cell to execute the cell\n']
            }
            for(let i = 0; i < tests.length; i++){
                s += tests[i];
            }
            this.editor.model.value.text = s;

        } else {
            console.warn('Celltests: Null cell warning');
        }
    }


    saveTestsForActiveCell(): void {
        /* if currentActiveCell exists */
        if(this.currentActiveCell !== null){
            let tests = [];
            let splits = this.editor.model.value.text.split(/\n/);
            for(let i=0; i<splits.length; i++){
                tests.push(splits[i] + '\n');
            }
            this.currentActiveCell.model.metadata.set('tests', tests);
        } else {
            console.warn('Celltests: Null cell warning');
        }
    }

    deleteTestsForActiveCell(): void {
        if(this.currentActiveCell !== null){
            this.currentActiveCell.model.metadata.delete('tests');
        } else {
            console.warn('Celltests: Null cell warning');
        }
    }

    loadRulesForCurrentNotebook(): void {
        if(this.notebookTracker !== null){
            let metadata: {[key: string]: string|number};
            metadata = this.notebookTracker.currentWidget.model.metadata.get('celltests') as {[key: string]: string|number} || {};
            for(let key of [].slice.call(Object.keys(metadata))){
                this.rules.setValuesByKey(key, true, metadata[key]);
            }
        } else {
            console.warn('Celltests: Null notebook warning');
        }
    }


    saveRulesForCurrentNotebook(): void {
        if(this.notebookTracker !== null){
            let metadata = {} as {[key: string]: string | number};
            let rules = ['lines_per_cell', 'cells_per_notebook', 'function_definitions', 'class_definitions', 'cell_coverage']
            for(let rule of [].slice.call(rules)){
                let settings = this.rules.getValuesByKey(rule);
                if(settings.enabled){
                    metadata[rule.key] = rule.value;
                }
            }
            this.notebookTracker.currentWidget.model.metadata.set('celltests', metadata);
        } else {
            console.warn('Celltests: Null notebook warning');
        }
    }

    get editorWidget(): CodeEditorWrapper {
        return this.editor;
    }

    editor: CodeEditorWrapper = null;
    rules: RulesWidget;
    currentActiveCell: Cell = null;
    notebookTracker: INotebookTracker = null;
}


export namespace Private {
}