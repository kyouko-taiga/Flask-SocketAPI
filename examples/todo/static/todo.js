'use strict';

var todolist = $('#todolist');
var socket = io.connect('http://' + document.domain + ':' + location.port);

socket.on('connect', function() {
    // Subscribe to the todo list.
    socket.emit('subscribe', 'todo/');

    $('#todoform').on('submit', function(e) {
        e.preventDefault();

        var input = $(this).find('input[type="text"]');
        var text = input.val();
        socket.emit('create', {
            uri: 'todo/',
            attributes: {
                text: text
            }
        });

        input.val('');
    });

    socket.on('create', function(payload) {
        // Create the todo HTML element.
        var todo = $(
            '<li id="todo' + payload.resource.id + '" class="list-group-item clearfix">' +
              '<div class="checkbox pull-left">' +
                '<label>' +
                  '<input type="checkbox"> ' + payload.resource.text +
                '</label>' +
              '</div>' +
            '</li>'
        );
        todolist.append(todo);

        // Emit a patch request when the checkbox is clicked.
        todo.find('input[type="checkbox"]').bind('click', function(e) {
            socket.emit('patch', {
                uri: 'todo/' + payload.resource.id,
                patch: {
                    completed: e.target.checked
                }
            });
        });
    });

    socket.on('patch', function(payload) {
        // Retreive and update the todo element.
        var todo = $('#todo' + payload.uri.split('/')[1])
        for (var attribute in payload.patch) {
            if (attribute == 'completed') {
                todo.find('input[type="checkbox"]').prop('checked', payload.patch[attribute])
            }
        }
    });

    socket.on('delete', function(payload) {
        // Retreive and delete the todo element.
        var todo = $('#todo' + payload.uri.split('/')[1])
        todo.remove();
    });
});
