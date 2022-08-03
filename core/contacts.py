import copy

from PyQt5.QtGui import QPixmap

import config


buddies = [
        {
            'id': '1', 'position': 0, 'icon': config.Gui.ICON_SETTINGS, 'name': 'Unknown Person',
            'message': 'Lorem ipsum.', 'group': 3, 'status': config.STATUS_ONLINE,
         },
        {
            'id': '3', 'position': 1, 'icon': config.Gui.ICON_APP, 'name': 'My Friend',
            'message': 'Hello, World!', 'group': 1, 'status': config.STATUS_ONLINE,
        },
        {
            'id': '2', 'position': 2, 'icon': config.Gui.ICON_SETTINGS, 'name': 'My Colleague',
            'message': 'I like OnionChat. Hope you will like it too!', 'group': 2, 'status': config.STATUS_OFFLINE,
        }
]

groups = ['Everyone', 'Friends', 'Colleagues', 'Unknown']

messages = {
    '1': ['Hello!', 'How are you?'],
    '2': ['Hi!'],
    '3': [],
}


def shorten_hostname(hostname: str, length: int = 10):
    return hostname[:length] + '…' + hostname[-length:]


def get_buddies(group: int = 0, status: int = config.STATUS_ALL) -> list:
    buddies_list = copy.deepcopy(buddies)
    # Filter groups
    # For 0 is for Everyone group, we filter 'Not-Everyone'
    if group:
        buddies_filtered = []
        for buddy in buddies_list:
            if buddy['group'] == group:
                buddies_filtered.append(buddy)
        buddies_list = buddies_filtered

    # Now check buddies status
    # If All selected then do not filter the results
    if status == config.STATUS_ALL:
        for buddy in buddies_list:
            buddy['icon'] = QPixmap(buddy['icon'])
        return buddies_list
    # If status selected (other than All), then filter the results accordingly
    else:
        buddies_result = []
        for buddy in buddies_list:
            if buddy['status'] == status:
                buddy['icon'] = QPixmap(buddy['icon'])
                buddies_result.append(buddy)
        return buddies_result


def get_messages(buddy_id) -> list:
    return messages[buddy_id]


def get_groups() -> list:
    return groups
