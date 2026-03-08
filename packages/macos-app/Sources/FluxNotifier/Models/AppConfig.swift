import Foundation

enum WindowPosition: String {
    case topRight = "top-right"
    case topLeft = "top-left"
    case bottomRight = "bottom-right"
    case bottomLeft = "bottom-left"
    case center = "center"
}

struct AppConfig {
    let windowPosition: WindowPosition
    let autoDismiss: Int

    static let `default` = AppConfig(windowPosition: .topRight, autoDismiss: 30)

    static func load() -> AppConfig {
        let home = FileManager.default.homeDirectoryForCurrentUser.path
        let path = "\(home)/.flux-notifier/config.toml"
        guard let data = FileManager.default.contents(atPath: path),
              let text = String(data: data, encoding: .utf8) else {
            return .default
        }
        return parse(toml: text)
    }

    private static func parse(toml: String) -> AppConfig {
        var inMacosSection = false
        var position: WindowPosition = .topRight
        var dismiss: Int = 30

        for line in toml.components(separatedBy: .newlines) {
            let trimmed = line.trimmingCharacters(in: .whitespaces)
            if trimmed.hasPrefix("[") {
                inMacosSection = trimmed == "[macos]"
                continue
            }
            guard inMacosSection else { continue }

            let parts = trimmed.components(separatedBy: "=")
            guard parts.count >= 2 else { continue }
            let key = parts[0].trimmingCharacters(in: .whitespaces)
            let value = parts[1...].joined(separator: "=")
                .trimmingCharacters(in: .whitespaces)
                .trimmingCharacters(in: CharacterSet(charactersIn: "\""))

            switch key {
            case "window_position":
                position = WindowPosition(rawValue: value) ?? .topRight
            case "auto_dismiss":
                dismiss = Int(value) ?? 30
            default:
                break
            }
        }
        return AppConfig(windowPosition: position, autoDismiss: dismiss)
    }
}
