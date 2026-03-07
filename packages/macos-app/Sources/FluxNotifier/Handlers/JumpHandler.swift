import AppKit

struct JumpHandler {
    static func open(_ jumpTo: JumpTo) {
        switch jumpTo.type {
        case .url, .vscode, .pycharm:
            guard let url = URL(string: jumpTo.target) else { return }
            NSWorkspace.shared.open(url)
        case .terminal:
            openInTerminal(command: jumpTo.target)
        }
    }

    private static func openInTerminal(command: String) {
        let escaped = command.replacingOccurrences(of: "\"", with: "\\\"")
        let source = "tell application \"Terminal\"\nactivate\ndo script \"\(escaped)\"\nend tell"
        if let appleScript = NSAppleScript(source: source) {
            var error: NSDictionary?
            appleScript.executeAndReturnError(&error)
        }
    }
}
