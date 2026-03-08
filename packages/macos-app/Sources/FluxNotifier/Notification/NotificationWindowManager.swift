import AppKit
import SwiftUI

@MainActor
final class NotificationWindowManager {
    static let shared = NotificationWindowManager()

    private var windows: [String: NSPanel] = [:]
    private var queue: [NotificationPayload] = []
    private var isPresenting = false

    private init() {}

    func show(payload: NotificationPayload) {
        queue.append(payload)
        presentNext()
    }

    private func presentNext() {
        guard !isPresenting, !queue.isEmpty else { return }
        let payload = queue.removeFirst()
        isPresenting = true
        presentWindow(payload: payload)
    }

    private func presentWindow(payload: NotificationPayload) {
        let panel = NSPanel(
            contentRect: .zero,
            styleMask: [.nonactivatingPanel, .fullSizeContentView, .borderless],
            backing: .buffered,
            defer: false
        )

        panel.isOpaque = false
        panel.backgroundColor = .clear
        panel.hasShadow = false
        panel.level = NSWindow.Level(rawValue: Int(CGWindowLevelForKey(.popUpMenuWindow)))
        panel.collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary]
        panel.isMovableByWindowBackground = true

        let windowId = payload.id
        let manager = self
        let ttl = payload.metadata?.ttl.map(Double.init) ?? 30

        let rootView = NotifyWindowView(payload: payload, ttl: ttl) { actionId in
            Task { @MainActor in
                ResponseHandler.respond(to: payload, actionId: actionId)
                manager.dismiss(id: windowId)
            }
        }
        .ignoresSafeArea()

        let sizeHint = CGSize(width: 380, height: 800)
        let hostingView = NSHostingView(rootView: rootView)
        hostingView.frame = CGRect(origin: .zero, size: sizeHint)
        panel.contentView = hostingView

        hostingView.layout()
        let fittingHeight = max(hostingView.fittingSize.height, 80)
        let size = CGSize(width: 380, height: fittingHeight)
        panel.setContentSize(size)
        hostingView.frame = CGRect(origin: .zero, size: size)

        positionPanel(panel)
        panel.orderFront(nil)
        NSApp.activate(ignoringOtherApps: false)
        windows[windowId] = panel

        if ttl > 0 {
            Task { @MainActor in
                try? await Task.sleep(nanoseconds: UInt64(ttl * 1_000_000_000))
                if manager.windows[windowId] != nil {
                    ResponseHandler.respond(to: payload, actionId: nil)
                    manager.dismiss(id: windowId)
                }
            }
        }
    }

    private func positionPanel(_ panel: NSPanel) {
        let screen = NSScreen.main ?? NSScreen.screens.first
        let margin: CGFloat = 16
        let area = screen?.visibleFrame ?? CGRect(x: 0, y: 0, width: 1440, height: 900)
        let size = panel.frame.size
        let config = AppConfig.load()

        let x: CGFloat
        let y: CGFloat

        switch config.windowPosition {
        case .topRight:
            x = area.maxX - size.width - margin
            y = area.maxY - size.height - margin
        case .topLeft:
            x = area.minX + margin
            y = area.maxY - size.height - margin
        case .bottomRight:
            x = area.maxX - size.width - margin
            y = area.minY + margin
        case .bottomLeft:
            x = area.minX + margin
            y = area.minY + margin
        case .center:
            x = area.midX - size.width / 2
            y = area.midY - size.height / 2
        }

        panel.setFrameOrigin(NSPoint(x: x, y: y))
    }

    private func dismiss(id: String) {
        guard let panel = windows.removeValue(forKey: id) else { return }

        NSAnimationContext.runAnimationGroup { ctx in
            ctx.duration = 0.25
            panel.animator().alphaValue = 0
        } completionHandler: { [weak self] in
            panel.orderOut(nil)
            Task { @MainActor [weak self] in
                self?.isPresenting = false
                self?.presentNext()
            }
        }
    }
}
