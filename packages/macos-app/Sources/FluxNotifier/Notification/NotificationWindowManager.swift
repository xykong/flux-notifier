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
        panel.level = .floating
        panel.collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary]
        panel.isMovableByWindowBackground = true

        let windowId = payload.id
        let manager = self

        let rootView = NotifyWindowView(payload: payload) { actionId in
            Task { @MainActor in
                ResponseHandler.respond(to: payload, actionId: actionId)
                manager.dismiss(id: windowId)
            }
        }
        .ignoresSafeArea()

        let hostingView = NSHostingView(rootView: rootView)
        hostingView.translatesAutoresizingMaskIntoConstraints = false
        panel.contentView = hostingView

        let size = CGSize(width: 360, height: hostingView.fittingSize.height)
        panel.setContentSize(size)

        positionPanel(panel)
        panel.orderFront(nil)
        windows[windowId] = panel

        let ttl = payload.metadata?.ttl.map(Double.init) ?? 30
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
        guard let screen = NSScreen.main else { return }
        let margin: CGFloat = 16
        let safeArea = screen.visibleFrame
        let size = panel.frame.size

        let x = safeArea.maxX - size.width - margin
        let y = safeArea.maxY - size.height - margin
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
