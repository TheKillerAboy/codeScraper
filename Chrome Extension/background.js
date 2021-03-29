var server = "http://127.0.0.1:7532"

chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.sync.set({ server });
  console.log(`Default background server set to ${server}`);
});