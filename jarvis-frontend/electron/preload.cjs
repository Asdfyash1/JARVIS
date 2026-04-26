const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('jarvisShell', {
  openExternal: (url) => ipcRenderer.invoke('open-external', url)
});
