/******************************************************************************
 *
 * Copyright (c) 2019, the nbcelltest authors.
 *
 * This file is part of the nbcelltest library, distributed under the terms of
 * the Apache License 2.0.  The full license can be found in the LICENSE file.
 *
 */
import { Dialog, showDialog } from "@jupyterlab/apputils";
import { Widget } from "@lumino/widgets";

import { ServerConnection } from "@jupyterlab/services";
import { JupyterFrontEnd } from "@jupyterlab/application";
import { IDocumentManager } from "@jupyterlab/docmanager";

export async function runCellTests(app: JupyterFrontEnd, docManager: IDocumentManager) {
  const result = await showDialog({
    buttons: [Dialog.cancelButton(), Dialog.okButton({ label: "Ok" })],
    title: "Run tests?",
  });
  if (result.button.label === "Cancel") {
    return;
  }
  if (!app.shell.currentWidget) {
    return;
  }
  const context = docManager.contextForWidget(app.shell.currentWidget);

  if (context === undefined) {
    return;
  }

  const path = context.path;
  const model = context.model.toJSON();

  const settings = ServerConnection.makeSettings();
  const res = await ServerConnection.makeRequest(`${settings.baseUrl}celltests/test/run`, { method: "post", body: JSON.stringify({ path, model }) }, settings);

  if (res.ok) {
    const iframe = document.createElement("iframe");
    const html_data: string = (await res.json()).test;
    iframe.onload = () => {
      // write iframe content
      iframe.contentWindow?.document.write(html_data);
    };
    const body = new Widget({ node: iframe });

    const dialog = new Dialog({
      body,
      buttons: [Dialog.okButton({ label: "Ok" })],
      title: "Tests run!",
    });

    (dialog.node.lastChild as HTMLDivElement).style.maxHeight = "1600px";
    (dialog.node.lastChild as HTMLDivElement).style.maxWidth = "2000px";
    (dialog.node.lastChild as HTMLDivElement).style.width = "900px";
    (dialog.node.lastChild as HTMLDivElement).style.height = "900px";

    await dialog.launch();
  } else {
    await showDialog({
      body: "Check the Jupyter logs for the exception.",
      buttons: [Dialog.okButton({ label: "Ok" })],
      title: "Something went wrong!",
    });
  }
}

export async function runCellLints(app: JupyterFrontEnd, docManager: IDocumentManager) {
  const result = await showDialog({
    buttons: [Dialog.cancelButton(), Dialog.okButton({ label: "Ok" })],
    title: "Run Lint?",
  });

  if (result.button.label === "Cancel") {
    return;
  }
  if (!app.shell.currentWidget) {
    return;
  }
  const context = docManager.contextForWidget(app.shell.currentWidget);
  if (context === undefined) {
    return;
  }

  const path = context.path;
  const model = context.model.toJSON();

  const settings = ServerConnection.makeSettings();
  const res = await ServerConnection.makeRequest(`${settings.baseUrl}celltests/lint/run`, { method: "post", body: JSON.stringify({ path, model }) }, settings);

  if (res.ok) {
    const div = document.createElement("div");
    div.innerHTML = (await res.json()).lint;
    const body = new Widget({ node: div });

    const dialog = new Dialog({
      body,
      buttons: [Dialog.okButton({ label: "Ok" })],
      title: "Lints run!",
    });

    (dialog.node.lastChild as HTMLDivElement).style.maxHeight = "1600px";
    (dialog.node.lastChild as HTMLDivElement).style.maxWidth = "2000px";
    (dialog.node.lastChild as HTMLDivElement).style.width = "600px";
    (dialog.node.lastChild as HTMLDivElement).style.height = "800px";

    await dialog.launch();
  } else {
    await showDialog({
      body: "Check the Jupyter logs for the exception.",
      buttons: [Dialog.okButton({ label: "Ok" })],
      title: "Something went wrong!",
    });
  }
}
