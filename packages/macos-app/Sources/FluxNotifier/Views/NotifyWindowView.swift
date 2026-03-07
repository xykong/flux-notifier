import SwiftUI

struct NotifyWindowView: View {
    let payload: NotificationPayload
    let onAction: (String?) -> Void

    @State private var imageLoaded: NSImage? = nil
    @State private var isHovered = false

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            headerBar
            content
            if payload.hasActions {
                actionBar
            }
        }
        .frame(width: 360)
        .background(
            RoundedRectangle(cornerRadius: 16, style: .continuous)
                .fill(.regularMaterial)
        )
        .overlay(
            RoundedRectangle(cornerRadius: 16, style: .continuous)
                .strokeBorder(Color.primary.opacity(0.08), lineWidth: 1)
        )
        .shadow(color: .black.opacity(0.25), radius: 20, x: 0, y: 8)
        .scaleEffect(isHovered ? 1.005 : 1.0)
        .animation(.spring(response: 0.25, dampingFraction: 0.8), value: isHovered)
        .onHover { isHovered = $0 }
    }

    private var headerBar: some View {
        HStack(spacing: 8) {
            eventIcon
                .frame(width: 28, height: 28)

            Text(payload.title)
                .font(.system(size: 13, weight: .semibold))
                .foregroundStyle(.primary)
                .lineLimit(2)

            Spacer()

            Button {
                onAction(nil)
            } label: {
                Image(systemName: "xmark.circle.fill")
                    .foregroundStyle(.secondary)
                    .imageScale(.medium)
            }
            .buttonStyle(.plain)
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 12)
    }

    private var eventIcon: some View {
        ZStack {
            Circle()
                .fill(iconBackground)
                .frame(width: 28, height: 28)
            Image(systemName: iconName)
                .foregroundStyle(iconForeground)
                .imageScale(.small)
                .fontWeight(.medium)
        }
    }

    private var content: some View {
        VStack(alignment: .leading, spacing: 10) {
            if let body = payload.body, !body.isEmpty {
                Text(AttributedString(markdownBody: body))
                    .font(.system(size: 12))
                    .foregroundStyle(.secondary)
                    .fixedSize(horizontal: false, vertical: true)
                    .lineLimit(8)
            }

            if let image = payload.image {
                AsyncImageView(urlString: image.url, alt: image.alt)
                    .frame(maxWidth: .infinity)
                    .frame(height: 140)
                    .clipShape(RoundedRectangle(cornerRadius: 8, style: .continuous))
            }
        }
        .padding(.horizontal, 14)
        .padding(.bottom, payload.hasActions ? 10 : 14)
    }

    private var actionBar: some View {
        HStack(spacing: 8) {
            Spacer()
            ForEach(payload.actions) { action in
                ActionButton(action: action) {
                    if let jumpTo = action.jump_to {
                        JumpHandler.open(jumpTo)
                    }
                    onAction(action.id)
                }
            }
        }
        .padding(.horizontal, 14)
        .padding(.bottom, 14)
    }

    private var iconName: String {
        switch payload.event_type {
        case .completion: "checkmark"
        case .choice: "questionmark"
        case .step: "arrow.right"
        case .input_required: "keyboard"
        case .info: "info"
        case .warning: "exclamationmark"
        case .error: "xmark"
        }
    }

    private var iconBackground: Color {
        switch payload.event_type {
        case .completion: .green.opacity(0.15)
        case .choice: .blue.opacity(0.15)
        case .step: .purple.opacity(0.15)
        case .input_required: .orange.opacity(0.15)
        case .info: .gray.opacity(0.15)
        case .warning: .yellow.opacity(0.15)
        case .error: .red.opacity(0.15)
        }
    }

    private var iconForeground: Color {
        switch payload.event_type {
        case .completion: .green
        case .choice: .blue
        case .step: .purple
        case .input_required: .orange
        case .info: .gray
        case .warning: .yellow
        case .error: .red
        }
    }
}

struct ActionButton: View {
    let action: NotifyAction
    let onTap: () -> Void
    @State private var isHovered = false

    var body: some View {
        Button(action: onTap) {
            Text(action.label)
                .font(.system(size: 12, weight: .medium))
                .padding(.horizontal, 14)
                .padding(.vertical, 6)
                .background(buttonBackground)
                .foregroundStyle(buttonForeground)
                .clipShape(RoundedRectangle(cornerRadius: 7, style: .continuous))
        }
        .buttonStyle(.plain)
        .scaleEffect(isHovered ? 0.97 : 1.0)
        .animation(.spring(response: 0.2), value: isHovered)
        .onHover { isHovered = $0 }
    }

    private var buttonBackground: Color {
        switch action.style {
        case .primary: return .accentColor
        case .destructive: return .red
        case .default: return Color.primary.opacity(isHovered ? 0.12 : 0.08)
        }
    }

    private var buttonForeground: Color {
        switch action.style {
        case .primary, .destructive: return .white
        case .default: return .primary
        }
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
                    Color.secondary.opacity(0.1)
                    if let alt {
                        Text(alt)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    } else {
                        ProgressView()
                            .scaleEffect(0.7)
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
