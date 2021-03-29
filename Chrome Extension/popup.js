const socket = io("http://localhost:7532/");
const socket_root_folder = io("http://localhost:7532/root-folder");

socket.on('connect', function() {
    $('#connection-show').text("Connected")
    $('#connection-show').removeClass("text-danger")
    $('#connection-show').addClass("text-success")

    socket_root_folder.emit('update root folder',{'change':false});
});

socket.on('disconnect', function() {
    $('#connection-show').text("Not Connected")
    $('#connection-show').addClass("text-danger")
    $('#connection-show').removeClass("text-success")
});

socket_root_folder.on('updated root folder', function(data){
    $('#root-folder').val(data['contest-root-folder'])
})

$('#update-root').click(function(){
    socket_root_folder.emit('update root folder',{'change':true,'contest-root-folder':$('#root-folder').val()})
})

chrome.fileSystem.chooseEntry({type: 'openFile', accepts: accepts}, function(entry) {
    if (!entry) {
      console.log("Cancelled");
      return;
    }
    // All of Chrome API is asynchronous! Use callbacks:
    chrome.fileSystem.getDisplayPath(entry, function(path) {
        console.log(path);
        // do something with path
    });
})
