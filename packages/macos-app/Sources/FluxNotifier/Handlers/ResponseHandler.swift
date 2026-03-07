import Foundation

struct ResponseHandler {
    private static var responsesDir: URL {
        let home = FileManager.default.homeDirectoryForCurrentUser
        return home.appendingPathComponent(".flux-notifier/responses")
    }

    static func write(response: UserResponse) {
        let dir = responsesDir
        try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)

        let file = dir.appendingPathComponent("\(response.notification_id).json")
        guard let data = try? JSONEncoder().encode(response) else { return }
        try? data.write(to: file, options: .atomic)
    }

    static func respond(to payload: NotificationPayload, actionId: String?) {
        let response = UserResponse.make(notificationId: payload.id, actionId: actionId)
        write(response: response)
    }
}
