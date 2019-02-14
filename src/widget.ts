import { Widget, PanelLayout, BoxPanel } from '@phosphor/widgets';

import { Cell, CodeCellModel } from '@jupyterlab/cells';
import { editorServices } from '@jupyterlab/codemirror';
import { CodeEditorWrapper} from '@jupyterlab/codeeditor';

import {CELLTEST_TOOL_CLASS, CELLTEST_TOOL_OPTIONS_CLASS, CELLTEST_TOOL_EDITOR_CLASS} from './utils';

/**
 * Widget responsible for holding test controls
 *
 * @class      OptionsWidget (name)
 */
class OptionsWidget extends BoxPanel {
    constructor() {
        super({direction: 'top-to-bottom'});

        /* Section Header */
        let label = document.createElement('label')
        label.textContent = 'Celltests';

        this.node.appendChild(label);
        this.node.classList.add(CELLTEST_TOOL_OPTIONS_CLASS);

        /* Add button */
        let div = document.createElement('div');
        let add = document.createElement('button');
        add.textContent = 'Add';
        add.onclick = () => {
            this.add();
        }

        /* Save button */
        let save = document.createElement('button');
        save.textContent = 'Save';
        save.onclick = () => {
            this.save();
        }

        /* Clear button */
        let clear = document.createElement('button');
        clear.textContent = 'Clear';
        clear.onclick = () => {
            this.clear();
        }

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
        let options = new OptionsWidget();

        /* create codemirror editor */
        let editorOptions = { model: new CodeCellModel({}), factory: editorServices.factoryService.newInlineEditor };
        let editor = (this.editor = new CodeEditorWrapper(editorOptions));
        editor.addClass(CELLTEST_TOOL_EDITOR_CLASS);
        editor.model.mimeType = 'text/x-ipython';

        /* add options and editor to widget */
        layout.addWidget(options);
        layout.addWidget(editor);

        /* set add button functionality */
        options.add = () => {
            this.fetchAndSetTests();
            return true;
        }

        /* set save button functionality */
        options.save = () => {
            this.saveTestsForActiveCell();
            return true;
        }

        options.clear = () => {
            this.deleteTestsForActiveCell();
            return true;
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
        if (this.currentActiveCell != null) {
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
        if(this.currentActiveCell != null){
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
        if(this.currentActiveCell != null){
            this.currentActiveCell.model.metadata.delete('tests');
        } else {
            console.warn('Celltests: Null cell warning');
        }
    }

    get editorWidget(): CodeEditorWrapper {
        return this.editor;
    }

    editor: CodeEditorWrapper = null;
    currentActiveCell: Cell = null;
}


export namespace Private {
}