import SwiftUI

@main
struct RichRankApp: App {
    @State private var appState = AppState()
    @State private var didBootstrap = false
    private let isUITesting = ProcessInfo.processInfo.arguments.contains("UI-Testing")

    var body: some Scene {
        WindowGroup {
            RootView()
                .environment(appState)
                .task {
                    if !didBootstrap {
                        didBootstrap = true
                        if isUITesting {
                            appState.route = .welcome
                        } else {
                            await appState.bootstrap()
                        }
                    }
                }
        }
    }
}

struct RootView: View {
    @Environment(AppState.self) private var app

    var body: some View {
        Group {
            switch app.route {
            case .welcome:
                WelcomeView()
            case .signup:
                SignupView()
            case .login:
                LoginView()
            case .connectBank:
                ConnectBankView()
            case .leaderboard:
                LeaderboardView()
            }
        }
        .animation(.easeInOut(duration: 0.2), value: app.route)
    }
}
