import UserNotifications
import AppKit

final class SystemNotificationManager: NSObject, UNUserNotificationCenterDelegate {
    static let shared = SystemNotificationManager()

    private override init() {
        super.init()
        UNUserNotificationCenter.current().delegate = self
    }

    func requestPermission() {
        UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound, .badge]) { _, _ in }
    }

    func post(payload: NotificationPayload) {
        let content = UNMutableNotificationContent()
        content.title = payload.title
        if let body = payload.body {
            let stripped = body
                .replacingOccurrences(of: "\\*\\*(.+?)\\*\\*", with: "$1", options: .regularExpression)
                .replacingOccurrences(of: "`(.+?)`", with: "$1", options: .regularExpression)
            content.body = stripped
        }
        content.sound = payload.priority == .urgent ? .defaultCritical : .default

        let request = UNNotificationRequest(
            identifier: payload.id,
            content: content,
            trigger: nil
        )
        UNUserNotificationCenter.current().add(request)
    }

    func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        willPresent notification: UNNotification,
        withCompletionHandler completionHandler: @escaping (UNNotificationPresentationOptions) -> Void
    ) {
        completionHandler([.banner, .sound])
    }
}
