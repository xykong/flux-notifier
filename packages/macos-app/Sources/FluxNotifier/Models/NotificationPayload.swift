import Foundation

enum EventType: String, Codable {
    case completion, choice, step, input_required, info, warning, error
}

enum ActionStyle: String, Codable {
    case primary, destructive, `default`
}

enum JumpToType: String, Codable {
    case url, vscode, pycharm, terminal
}

enum Priority: String, Codable {
    case low, normal, high, urgent
}

struct JumpTo: Codable {
    let type: JumpToType
    let target: String
}

struct NotifyAction: Codable, Identifiable {
    let id: String
    let label: String
    let style: ActionStyle
    let jump_to: JumpTo?

    init(id: String, label: String, style: ActionStyle = .default, jump_to: JumpTo? = nil) {
        self.id = id
        self.label = label
        self.style = style
        self.jump_to = jump_to
    }
}

struct NotifyImage: Codable {
    let url: String
    let alt: String?
    let width: Int?
    let height: Int?
}

struct NotifyMetadata: Codable {
    let source_app: String?
    let session_id: String?
    let priority: Priority?
    let ttl: Int?
    let tags: [String]?
}

struct NotificationPayload: Codable, Identifiable {
    let version: String
    let id: String
    let timestamp: String?
    let event_type: EventType
    let title: String
    let body: String?
    let image: NotifyImage?
    let actions: [NotifyAction]
    let metadata: NotifyMetadata?

    var hasActions: Bool { !actions.isEmpty }

    var priority: Priority {
        metadata?.priority ?? .normal
    }
}

struct UserResponse: Codable {
    let notification_id: String
    let action_id: String?
    let timestamp: String
    let source_terminal: String
    let timeout: Bool

    static func make(notificationId: String, actionId: String?) -> UserResponse {
        let formatter = ISO8601DateFormatter()
        return UserResponse(
            notification_id: notificationId,
            action_id: actionId,
            timestamp: formatter.string(from: Date()),
            source_terminal: "macos",
            timeout: false
        )
    }
}
