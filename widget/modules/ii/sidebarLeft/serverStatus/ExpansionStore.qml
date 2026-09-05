import QtQuick

/**
 * Remembers which sections are expanded.
 */
QtObject {
    id: root

    property var state: ({})

    function get(key, fallback) {
        const value = root.state[key];
        return value === undefined ? fallback : value;
    }

    function set(key, value) {
        root.state[key] = value;
    }
}
