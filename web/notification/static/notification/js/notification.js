function connectNotificationSocket() {
    const notificationSocket = new WebSocket('ws://' + window.location.host + '/ws/notification/');

    notificationSocket.onopen = () => {
        // When the socket is open, request the first page of notifications.
        notificationSocket.send(
            JSON.stringify({
                type: 'page',
                page: 1
            })
        );

        let $notificationArea = $('#notificationArea');

        $notificationArea.scrollTop($notificationArea[0].scrollHeight);
    }

    notificationSocket.onmessage = (e) => {
        const data = JSON.parse(e.data);
        const {id, type, code, unread_count, total_count, html} = data;

        console.log(data);

        const $notificationArea = $('#notificationArea');
        const $notificationNumber = $('#notificationNumber');
        const $notificationActions = $('#notificationActions');
        const $notificationEmptyDisplay = $('#notificationEmptyDisplay');
        const $notificationShowMore = $('#notificationShowMore');

        $notificationNumber.text(unread_count).toggle(unread_count >= 1);

        // Handle the incoming message types
        if (type === 'notification') {
            // Populate our notifications and replace existing ones
            $(html).find('li').each((i, e) => {
                let $note = $(e);
                let id = $note.data('id');
                let _note = $notificationArea.find(`[data-id="${id}"]`).first();

                if (_note.length === 0) {
                    $notificationArea.append($note);
                } else {
                    _note.replaceWith($note);
                }
            });

            const $notificationItems = $notificationArea.find('li');

            $notificationItems.sort((a, b) => {
                return $(a).data('id') - $(b).data('id');
            });

            $notificationArea.empty().append($notificationItems);

        } else if (type === 'clear' && code === 200) {
            $notificationArea.empty();
        } else if (type === 'read' && code === 200) {
            const queryString = id ? `li[data-id="${id}"]` : `li[data-id]`;

            $notificationArea.find(queryString).removeClass('notification-unread');
        }

        const liCount = $notificationArea.find('li').length;
        $notificationArea.toggle(liCount > 0);
        $notificationActions.css('pointer-events', liCount > 0 ? 'auto' : 'none');
        $notificationEmptyDisplay.toggle(liCount === 0);
        $notificationShowMore.toggle(total_count - liCount > 0);
    };

    notificationSocket.onclose = (e) => {
        // Should the connection close, every 10 seconds try and reconnect to notification socket
        setTimeout(connectNotificationSocket, 10000);
    }

    $('#notificationArea').on('click', '.notification-container[data-id]', (e) => {
        let $notification = $(e.currentTarget),
             id = $notification.data('id'),
             url = $notification.data('url');

        if (id && $notification.hasClass('notification-unread')) {
            notificationSocket.send(
                JSON.stringify({
                    type: 'read',
                    id: id
                })
            );
        }

        if (url) {
            window.location.href = $notification.data('url');
        }
        return false;
    });

    $('#clearNotifications').click((e) => {
        if (!$(e.target).prop('disabled')) {
            notificationSocket.send(JSON.stringify({type: 'clear'}));
        }
        return false;
    });

    $('#readAllNotifications').click((e) => {
        if (!$(e.target).prop('disabled')) {
            notificationSocket.send(JSON.stringify({type: 'all_read'}));
        }
        return false;
    });

    $('#notificationShowMore').click((e) => {
        if (!$(e.target).prop('disabled')) {
            const liCount = $('#notificationArea').find('li').length;
            const pageNo = Math.floor(liCount / 5) + 1;

            notificationSocket.send(
                JSON.stringify({
                    type: 'page',
                    page: pageNo
                })
            );
        }
        return false;
    });
}

connectNotificationSocket();