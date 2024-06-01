/******************************************************************************
 *
 * Copyright (c) 2019, the nbcelltest authors.
 *
 * This file is part of the nbcelltest library, distributed under the terms of
 * the Apache License 2.0.  The full license can be found in the LICENSE file.
 *
 */
import {Dialog, showDialog} from "@jupyterlab/apputils";
import {Widget} from "@lumino/widgets";

import {ServerConnection} from "@jupyterlab/services";

export async function runCellTests(app, docManager) {
  const result = await showDialog({
    buttons: [Dialog.cancelButton(), Dialog.okButton({label: "Ok"})],
    title: "Run tests?",
  });
  if (result.button.label === "Cancel") {
    return;
  }
  const context = docManager.contextForWidget(app.shell.currentWidget);
  let path = "";
  let model = {};
  if (context) {
    path = context.path;
    model = context.model.toJSON();
  }

  const settings = ServerConnection.makeSettings();
  const res = await ServerConnection.makeRequest(`${settings.baseUrl}celltests/test/run`, {method: "post", body: {path, model}}, settings);

  if (res.ok) {
    const div = document.createElement("div");
    div.innerHTML = (await res.json()).test;
    const body = new Widget({node: div});

    const dialog = new Dialog({
      body,
      buttons: [Dialog.okButton({label: "Ok"})],
      title: "Tests run!",
    });
    dialog.node.lastChild.style.maxHeight = "750px";
    dialog.node.lastChild.style.maxWidth = "800px";
    dialog.node.lastChild.style.width = "800px";

    await dialog.launch();
  } else {
    await showDialog({
      body: "Check the Jupyter logs for the exception.",
      buttons: [Dialog.okButton({label: "Ok"})],
      title: "Something went wrong!",
    });
  }
}

export async function runCellLints(app, docManager) {
  const result = await showDialog({
    buttons: [Dialog.cancelButton(), Dialog.okButton({label: "Ok"})],
    title: "Run Lint?",
  });

  if (result.button.label === "Cancel") {
    return;
  }
  const context = docManager.contextForWidget(app.shell.currentWidget);
  let path = "";
  let model = {};
  if (context) {
    path = context.path;
    model = context.model.toJSON();
  }

  const settings = ServerConnection.makeSettings();
  const res = await ServerConnection.makeRequest(`${settings.baseUrl}celltests/lint/run`, {method: "post", body: {path, model}}, settings);

  if (res.ok) {
    const div = document.createElement("div");
    div.innerHTML = (await res.json()).lint;
    const body = new Widget({node: div});

    const dialog = new Dialog({
      body,
      buttons: [Dialog.okButton({label: "Ok"})],
      title: "Lints run!",
    });

    dialog.node.lastChild.style.maxHeight = "750px";
    dialog.node.lastChild.style.maxWidth = "500px";
    dialog.node.lastChild.style.width = "500px";

    await dialog.launch();
  } else {
    await showDialog({
      body: "Check the Jupyter logs for the exception.",
      buttons: [Dialog.okButton({label: "Ok"})],
      title: "Something went wrong!",
    });
  }
}
