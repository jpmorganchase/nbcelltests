import { Widget, PanelLayout, BoxPanel } from '@phosphor/widgets';

import { Cell, CodeCellModel } from '@jupyterlab/cells';
import { editorServices } from '@jupyterlab/codemirror';
import { CodeEditorWrapper} from '@jupyterlab/codeeditor';

import {CELLTEST_TOOL_CLASS, CELLTEST_TOOL_OPTIONS_CLASS, CELLTEST_TOOL_EDITOR_CLASS} from './utils';

class OptionsWidget extends BoxPanel {
    constructor() {
        super({direction: 'top-to-bottom'});

        let label = document.createElement('label')
        label.textContent = 'Celltests';

        this.node.appendChild(label);
        this.node.classList.add(CELLTEST_TOOL_OPTIONS_CLASS);

        let div = document.createElement('div');
        let add = document.createElement('button');
        add.textContent = 'Add';
        add.onclick = () => {
            this.add();
        }

        let save = document.createElement('button');
        save.textContent = 'Save';
        save.onclick = () => {
            this.save();
        }

        let clear = document.createElement('button');
        clear.textContent = 'Clear';
        clear.onclick = () => {
            this.clear();
        }

        div.appendChild(add);
        div.appendChild(save);
        div.appendChild(clear);
        this.node.appendChild(div);
    }

    add = ()=>{};
    save = ()=>{};
    clear = ()=>{};
}

export class CelltestsWidget extends Widget {
    constructor() {
        super()
        this.node.classList.add(CELLTEST_TOOL_CLASS);

        let options = new OptionsWidget();
        let layout = (this.layout = new PanelLayout());

        let editorOptions = { model: new CodeCellModel({}), factory: editorServices.factoryService.newInlineEditor };
        let editor = (this.editor = new CodeEditorWrapper(editorOptions));
        editor.addClass(CELLTEST_TOOL_EDITOR_CLASS);

        editor.model.mimeType = 'text/x-ipython';

        layout.addWidget(options);
        layout.addWidget(editor);

        options.add = () => {
            this.currentActiveCell.model.metadata.set('tests', []);
            this.editor.editor.setOption("readOnly", false);
            this.editor.editor.focus();
            return true;
        }

        options.save = () => {
            let tests = [];
            let splits = editor.model.value.text.split(/\n/);
            for(let i=0; i<splits.length; i++){
                tests.push(splits[i] + '\n');
            }

            if(this.currentActiveCell != null){
                this.currentActiveCell.model.metadata.set('tests', tests);
            } else {
                console.warn('Celltests: Null cell warning');
            }
            return true;
        }

        options.clear = () => {
            if(this.currentActiveCell != null){
                this.currentActiveCell.model.metadata.delete('tests');
            } else {
                console.warn('Celltests: Null cell warning');
            }
            return true;
        }
    }

    loadTestsForActiveCell(): void {
        if (this.currentActiveCell != null) {
            let tests = this.currentActiveCell.model.metadata.get('tests') as Array<string>;
            let s = '';
            if(tests === undefined){
                this.editor.editor.setOption("readOnly", true);
            } else {
                for(let i = 0; i < tests.length; i++){
                    s += tests[i];
                }
            }
            this.editor.model.value.text = s;

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