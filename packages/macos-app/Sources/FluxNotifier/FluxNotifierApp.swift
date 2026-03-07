import SwiftUI
import AppKit

@main
struct FluxNotifierApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) var delegate

    var body: some Scene {
        Settings {
            PreferencesView()
        }
    }
}

final class AppDelegate: NSObject, NSApplicationDelegate {
    private var statusItem: NSStatusItem?
    private var socketServer: UnixSocketListener?
    private let socketPath: String = {
        let home = FileManager.default.homeDirectoryForCurrentUser.path
        return "\(home)/.flux-notifier/macos.sock"
    }()

    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.accessory)

        setupStatusItem()
        setupSocketDirectory()
        startSocketServer()
        SystemNotificationManager.shared.requestPermission()
    }

    func applicationWillTerminate(_ notification: Notification) {
        socketServer?.stop()
    }

    private func setupStatusItem() {
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
        guard let button = statusItem?.button else { return }

        button.image = NSImage(systemSymbolName: "bell.fill", accessibilityDescription: "Flux Notifier")
        button.image?.isTemplate = true
        button.action = #selector(statusItemClicked)
        button.target = self
    }

    @objc private func statusItemClicked() {
        let menu = NSMenu()
        menu.addItem(NSMenuItem(title: "Flux Notifier v\(appVersion)", action: nil, keyEquivalent: ""))
        menu.addItem(.separator())
        menu.addItem(NSMenuItem(title: "Preferences...", action: #selector(openPreferences), keyEquivalent: ","))
        menu.addItem(.separator())
        menu.addItem(NSMenuItem(title: "Quit", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q"))
        statusItem?.menu = menu
        statusItem?.button?.performClick(nil)
        statusItem?.menu = nil
    }

    @objc private func openPreferences() {
        NSApp.activate(ignoringOtherApps: true)
        if #available(macOS 13, *) {
            NSApp.sendAction(Selector(("showSettingsWindow:")), to: nil, from: nil)
        } else {
            NSApp.sendAction(Selector(("showPreferencesWindow:")), to: nil, from: nil)
        }
    }

    private func setupSocketDirectory() {
        let dir = (socketPath as NSString).deletingLastPathComponent
        try? FileManager.default.createDirectory(atPath: dir, withIntermediateDirectories: true)
        try? FileManager.default.removeItem(atPath: socketPath)
    }

    private func startSocketServer() {
        let server = UnixSocketListener(socketPath: socketPath) { payload in
            Task { @MainActor in
                SystemNotificationManager.shared.post(payload: payload)
                NotificationWindowManager.shared.show(payload: payload)
            }
        }
        server.start()
        socketServer = server
    }

    private var appVersion: String {
        Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "0.1.0"
    }
}

struct PreferencesView: View {
    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Flux Notifier")
                .font(.title2.bold())

            Text("Receives notifications from AI programs and displays them on your Mac.")
                .foregroundStyle(.secondary)

            Divider()

            HStack {
                Text("Status")
                Spacer()
                HStack(spacing: 4) {
                    Circle()
                        .fill(.green)
                        .frame(width: 8, height: 8)
                    Text("Running")
                        .foregroundStyle(.secondary)
                }
            }
        }
        .padding(24)
        .frame(width: 400)
    }
}
