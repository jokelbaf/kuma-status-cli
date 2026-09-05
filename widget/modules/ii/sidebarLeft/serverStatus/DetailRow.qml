import qs.modules.common
import qs.modules.common.widgets
import QtQuick
import QtQuick.Layouts

/**
 * Label and value pair shown inside an expanded monitor.
 */
RowLayout {
    id: root

    required property string label
    required property string value

    spacing: 8

    StyledText {
        Layout.alignment: Qt.AlignTop
        text: root.label
        font.pixelSize: Appearance.font.pixelSize.smaller
        color: Appearance.colors.colOnLayer1Inactive
    }

    StyledText {
        Layout.fillWidth: true
        text: root.value
        font.pixelSize: Appearance.font.pixelSize.smaller
        color: Appearance.colors.colOnLayer2
        horizontalAlignment: Text.AlignRight
        wrapMode: Text.Wrap
    }
}
