import {Widget} from '@phosphor/widgets';
import {JupyterLab} from '@jupyterlab/application';
import {showDialog, Dialog} from '@jupyterlab/apputils';
import {PageConfig} from '@jupyterlab/coreutils'
import {IDocumentManager} from '@jupyterlab/docmanager';

import {request, RequestResult} from './request';


export
function runCellTests(app: JupyterLab, docManager: IDocumentManager): void {
    showDialog({
        title: 'Run tests?',
        // focusNodeSelector: 'input',
        buttons: [Dialog.cancelButton(), Dialog.okButton({ label: 'Ok' })]
    }).then(result => {
        if (result.button.label === 'CANCEL') {
            return;
        }
        const context = docManager.contextForWidget(app.shell.currentWidget);
        let path = '';
        let model = {};
        if(context){
            path = context.path; 
            model = context.model.toJSON();
        }

        return new Promise(function(resolve) {
            request('post',
                PageConfig.getBaseUrl() + "celltests/test/run",
                {},
                {'path': path, 'model': model}
                ).then((res:RequestResult) => {
                    if(res.ok){
                        let div = document.createElement('div');
                        div.innerHTML = (res.json() as {[key: string]: string})['test'];
                        let body = new Widget({node:div});

                        let dialog = new Dialog({
                            title: 'Tests run!',
                            body: body,
                            buttons: [Dialog.okButton({ label: 'Ok' })]
                        });
                        (dialog.node.lastChild as HTMLDivElement).style.maxHeight = '750px';
                        (dialog.node.lastChild as HTMLDivElement).style.maxWidth = '1000px';
                        (dialog.node.lastChild as HTMLDivElement).style.width = '1000px';

                        dialog.launch().then(() => {
                            resolve();
                        })
                    } else {
                        showDialog({
                            title: 'Something went wrong!',
                            body: 'Check the Jupyter logs for the exception.',
                            buttons: [Dialog.okButton({ label: 'Ok' })]
                        }).then(() => {resolve();})
                    }
                });
            });
        }
    );
}
