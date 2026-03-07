// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "FluxNotifier",
    platforms: [.macOS(.v13)],
    targets: [
        .executableTarget(
            name: "FluxNotifier",
            path: "Sources/FluxNotifier",
            swiftSettings: [
                .unsafeFlags(["-strict-concurrency=minimal"]),
            ]
        ),
    ]
)
