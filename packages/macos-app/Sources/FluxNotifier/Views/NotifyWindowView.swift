import SwiftUI
import AppKit

struct NotifyWindowView: View {
    let payload: NotificationPayload
    let ttl: Double
    let onAction: (String?) -> Void

    @State private var offsetX: CGFloat = 40
    @State private var progress: Double = 1.0
    @State private var secondsLeft: Int = 0

    var body: some View {
        mainContent
            .frame(width: 380)
            .offset(x: offsetX)
            .onAppear {
                withAnimation(.spring(response: 0.4, dampingFraction: 0.82)) {
                    offsetX = 0
                }
                guard ttl > 0 else { return }
                secondsLeft = Int(ceil(ttl))
                withAnimation(.linear(duration: ttl)) {
                    progress = 0
                }
            }
            .onReceive(
                Timer.publish(every: 1, on: .main, in: .common).autoconnect()
            ) { _ in
                guard ttl > 0, secondsLeft > 0 else { return }
                secondsLeft -= 1
            }
    }

    private var mainContent: some View {
        VStack(alignment: .leading, spacing: 0) {
            headerBar
            if payload.body != nil || payload.image != nil {
                contentArea
            }
            if payload.hasActions {
                actionBar
            }
            if ttl > 0 {
                countdownBar
            }
        }
        .background(Color.white)
        .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: 14, style: .continuous)
                .strokeBorder(Color.black.opacity(0.09), lineWidth: 1)
        )
        .shadow(color: Color.black.opacity(0.10), radius: 24, x: 0, y: 8)
        .shadow(color: Color.black.opacity(0.06), radius: 6, x: 0, y: 2)
    }

    private var countdownBar: some View {
        GeometryReader { geo in
            ZStack(alignment: .leading) {
                Color.black.opacity(0.05)
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                iconColor.opacity(0.5)
                    .frame(width: geo.size.width * progress, height: 3)
            }
        }
        .frame(height: 3)
    }

    private var headerBar: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack(alignment: .center, spacing: 8) {
                sourceLabel
                Spacer()
                if ttl > 0 {
                    Text("\(secondsLeft)s")
                        .font(.system(size: 11, weight: .medium).monospacedDigit())
                        .foregroundStyle(Color(white: 0.55))
                        .animation(nil, value: secondsLeft)
                }
                CloseButton(onClose: { onAction(nil) })
            }

            HStack(alignment: .top, spacing: 10) {
                eventIcon
                Text(payload.title)
                    .font(.system(size: 15, weight: .semibold))
                    .foregroundStyle(Color(white: 0.08))
                    .fixedSize(horizontal: false, vertical: true)
                    .lineLimit(3)
                    .textSelection(.enabled)
            }
        }
        .padding(.horizontal, 16)
        .padding(.top, 14)
        .padding(.bottom, 12)
    }

    private var sourceLabel: some View {
        let source = payload.metadata?.source_app ?? "Flux Notifier"
        return HStack(spacing: 5) {
            Circle()
                .fill(iconColor)
                .frame(width: 6, height: 6)
            Text(source)
                .font(.system(size: 11, weight: .medium))
                .foregroundStyle(iconColor)
        }
        .padding(.horizontal, 8)
        .padding(.vertical, 3)
        .background(iconColor.opacity(0.08))
        .clipShape(Capsule())
    }

    private var eventIcon: some View {
        ZStack {
            RoundedRectangle(cornerRadius: 7, style: .continuous)
                .fill(iconColor.opacity(0.12))
                .frame(width: 28, height: 28)
            Image(systemName: iconName)
                .foregroundStyle(iconColor)
                .font(.system(size: 12, weight: .semibold))
        }
    }

    private var contentArea: some View {
        VStack(alignment: .leading, spacing: 10) {
            if let body = payload.body, !body.isEmpty {
                Text(AttributedString(markdownBody: body))
                    .font(.system(size: 13))
                    .foregroundStyle(Color(white: 0.30))
                    .fixedSize(horizontal: false, vertical: true)
                    .lineLimit(8)
                    .lineSpacing(2)
                    .textSelection(.enabled)
            }
            if let image = payload.image {
                AsyncImageView(urlString: image.url, alt: image.alt)
                    .frame(maxWidth: .infinity)
                    .frame(height: 130)
                    .clipShape(RoundedRectangle(cornerRadius: 8, style: .continuous))
            }
        }
        .padding(.horizontal, 16)
        .padding(.bottom, 14)
    }

    private var actionBar: some View {
        VStack(spacing: 0) {
            Divider()
                .background(Color.black.opacity(0.06))
            HStack(spacing: 8) {
                ForEach(payload.actions) { action in
                    ActionButton(action: action, accentColor: iconColor) {
                        if let jumpTo = action.jump_to {
                            JumpHandler.open(jumpTo)
                        }
                        onAction(action.id)
                    }
                    .frame(maxWidth: .infinity)
                }
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 12)
        }
    }

    private var iconName: String {
        switch payload.event_type {
        case .completion:     return "checkmark"
        case .choice:         return "questionmark"
        case .step:           return "arrow.right"
        case .input_required: return "keyboard"
        case .info:           return "info"
        case .warning:        return "exclamationmark"
        case .error:          return "xmark"
        }
    }

    private var iconColor: Color {
        switch payload.event_type {
        case .completion:     return Color(red: 0.13, green: 0.69, blue: 0.34)
        case .choice:         return Color(red: 0.18, green: 0.44, blue: 0.93)
        case .step:           return Color(red: 0.55, green: 0.27, blue: 0.88)
        case .input_required: return Color(red: 0.95, green: 0.42, blue: 0.07)
        case .info:           return Color(red: 0.35, green: 0.38, blue: 0.44)
        case .warning:        return Color(red: 0.80, green: 0.58, blue: 0.02)
        case .error:          return Color(red: 0.88, green: 0.22, blue: 0.22)
        }
    }
}

struct CloseButton: View {
    let onClose: () -> Void
    @State private var isHovered = false

    var body: some View {
        Button(action: onClose) {
            Image(systemName: "xmark")
                .font(.system(size: 10, weight: .medium))
                .foregroundStyle(Color(white: isHovered ? 0.25 : 0.55))
                .frame(width: 20, height: 20)
                .background(Color.black.opacity(isHovered ? 0.07 : 0.04))
                .clipShape(Circle())
        }
        .buttonStyle(.plain)
        .onHover { isHovered = $0 }
        .animation(.easeInOut(duration: 0.15), value: isHovered)
        .contentShape(Circle())
    }
}

struct ActionButton: View {
    let action: NotifyAction
    let accentColor: Color
    let onTap: () -> Void
    @State private var isHovered = false

    var body: some View {
        Button(action: onTap) {
            Text(action.label)
                .font(.system(size: 13, weight: .medium))
                .foregroundStyle(buttonForeground)
                .frame(maxWidth: .infinity)
                .padding(.vertical, 7)
                .background(buttonBackground)
                .overlay(
                    RoundedRectangle(cornerRadius: 8, style: .continuous)
                        .strokeBorder(buttonBorder, lineWidth: 1)
                )
                .clipShape(RoundedRectangle(cornerRadius: 8, style: .continuous))
        }
        .buttonStyle(ScaleButtonStyle())
        .onHover { isHovered = $0 }
        .animation(.easeInOut(duration: 0.12), value: isHovered)
    }

    private var buttonBackground: Color {
        switch action.style {
        case .primary:     return isHovered ? accentColor.opacity(0.88) : accentColor
        case .destructive: return isHovered ? Color(red: 0.82, green: 0.15, blue: 0.15) : Color(red: 0.88, green: 0.22, blue: 0.22)
        case .default:     return isHovered ? Color.black.opacity(0.07) : Color.black.opacity(0.04)
        }
    }

    private var buttonForeground: Color {
        switch action.style {
        case .primary, .destructive: return .white
        case .default:               return Color(white: 0.15)
        }
    }

    private var buttonBorder: Color {
        switch action.style {
        case .primary, .destructive: return .clear
        case .default:               return Color.black.opacity(0.12)
        }
    }
}

struct ScaleButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .scaleEffect(configuration.isPressed ? 0.96 : 1.0)
            .animation(.spring(response: 0.25, dampingFraction: 0.7), value: configuration.isPressed)
    }
}

struct AsyncImageView: View {
    let urlString: String
    let alt: String?
    @State private var image: NSImage? = nil

    var body: some View {
        Group {
            if let img = image {
                Image(nsImage: img)
                    .resizable()
                    .scaledToFill()
            } else {
                ZStack {
                    Color.black.opacity(0.04)
                    if let alt {
                        Text(alt)
                            .font(.system(size: 12))
                            .foregroundStyle(Color(white: 0.55))
                    } else {
                        ProgressView()
                            .controlSize(.small)
                    }
                }
            }
        }
        .task {
            await loadImage()
        }
    }

    private func loadImage() async {
        if urlString.hasPrefix("data:") {
            guard let commaIndex = urlString.firstIndex(of: ",") else { return }
            let base64 = String(urlString[urlString.index(after: commaIndex)...])
            if let data = Data(base64Encoded: base64), let img = NSImage(data: data) {
                image = img
            }
            return
        }
        guard let url = URL(string: urlString) else { return }
        guard let (data, _) = try? await URLSession.shared.data(from: url),
              let img = NSImage(data: data) else { return }
        image = img
    }
}

extension AttributedString {
    init(markdownBody: String) {
        if let attr = try? AttributedString(
            markdown: markdownBody,
            options: .init(interpretedSyntax: .full)
        ) {
            self = attr
        } else {
            self = AttributedString(markdownBody)
        }
    }
}
