import Foundation
import Network

final class UnixSocketServer {
    private let socketPath: String
    private var listener: NWListener?
    private let onPayload: (NotificationPayload) -> Void

    init(socketPath: String, onPayload: @escaping (NotificationPayload) -> Void) {
        self.socketPath = socketPath
        self.onPayload = onPayload
    }

    func start() {
        cleanupSocket()

        guard let endpoint = NWEndpoint.unix(path: socketPath) as NWEndpoint?,
              case .unix = endpoint else { return }

        let params = NWParameters()
        params.defaultProtocolStack.transportProtocol = NWProtocolTCP.Options()

        let unixParams = NWParameters()
        unixParams.requiredLocalEndpoint = .unix(path: socketPath)

        do {
            listener = try NWListener(using: .tcp, on: .any)
        } catch {
            return
        }

        let path = socketPath
        let cb = onPayload

        let unixListener = startUnixListener(socketPath: path, onPayload: cb)
        self.listener = nil
        _ = unixListener
    }

    private func startUnixListener(
        socketPath: String,
        onPayload: @escaping (NotificationPayload) -> Void
    ) -> UnixSocketListener {
        let srv = UnixSocketListener(socketPath: socketPath, onPayload: onPayload)
        srv.start()
        return srv
    }

    func stop() {
        listener?.cancel()
        cleanupSocket()
    }

    private func cleanupSocket() {
        try? FileManager.default.removeItem(atPath: socketPath)
    }
}

final class UnixSocketListener {
    private let socketPath: String
    private let onPayload: (NotificationPayload) -> Void
    private var serverFd: Int32 = -1
    private var running = false

    init(socketPath: String, onPayload: @escaping (NotificationPayload) -> Void) {
        self.socketPath = socketPath
        self.onPayload = onPayload
    }

    func start() {
        running = true
        Thread.detachNewThread { [weak self] in
            self?.listenLoop()
        }
    }

    func stop() {
        running = false
        if serverFd >= 0 {
            close(serverFd)
            serverFd = -1
        }
        try? FileManager.default.removeItem(atPath: socketPath)
    }

    private func listenLoop() {
        let fd = socket(AF_UNIX, SOCK_STREAM, 0)
        guard fd >= 0 else { return }
        serverFd = fd

        var addr = sockaddr_un()
        addr.sun_family = sa_family_t(AF_UNIX)

        socketPath.withCString { ptr in
            withUnsafeMutablePointer(to: &addr.sun_path) { sunPath in
                sunPath.withMemoryRebound(to: CChar.self, capacity: 104) { dest in
                    _ = strlcpy(dest, ptr, 104)
                }
            }
        }

        let addrLen = socklen_t(MemoryLayout<sockaddr_un>.size)
        withUnsafePointer(to: &addr) { ptr in
            ptr.withMemoryRebound(to: sockaddr.self, capacity: 1) { sockPtr in
                _ = bind(fd, sockPtr, addrLen)
            }
        }

        listen(fd, 10)

        while running {
            let clientFd = accept(fd, nil, nil)
            guard clientFd >= 0 else { continue }
            Thread.detachNewThread { [weak self] in
                self?.handleClient(fd: clientFd)
            }
        }
    }

    private func handleClient(fd: Int32) {
        defer { close(fd) }

        var lengthBytes = [UInt8](repeating: 0, count: 4)
        guard readExact(fd: fd, buffer: &lengthBytes, count: 4) else {
            sendAck(fd: fd, ok: false, error: "failed to read length prefix")
            return
        }

        let length = Int(lengthBytes[0]) << 24
            | Int(lengthBytes[1]) << 16
            | Int(lengthBytes[2]) << 8
            | Int(lengthBytes[3])

        guard length > 0, length < 1_048_576 else {
            sendAck(fd: fd, ok: false, error: "invalid message length: \(length)")
            return
        }

        var body = [UInt8](repeating: 0, count: length)
        guard readExact(fd: fd, buffer: &body, count: length) else {
            sendAck(fd: fd, ok: false, error: "failed to read body")
            return
        }

        let data = Data(body)
        do {
            let payload = try JSONDecoder().decode(NotificationPayload.self, from: data)
            sendAck(fd: fd, ok: true, error: nil)
            DispatchQueue.main.async { [weak self] in
                self?.onPayload(payload)
            }
        } catch {
            sendAck(fd: fd, ok: false, error: "decode error: \(error.localizedDescription)")
        }
    }

    private func readExact(fd: Int32, buffer: inout [UInt8], count: Int) -> Bool {
        var totalRead = 0
        while totalRead < count {
            let n = recv(fd, &buffer[totalRead], count - totalRead, 0)
            if n <= 0 { return false }
            totalRead += n
        }
        return true
    }

    private func sendAck(fd: Int32, ok: Bool, error: String?) {
        var ack: [String: Any] = ["ok": ok]
        if let error { ack["error"] = error }
        guard let data = try? JSONSerialization.data(withJSONObject: ack) else { return }
        data.withUnsafeBytes { _ = send(fd, $0.baseAddress, data.count, 0) }
    }
}
