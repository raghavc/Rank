import SwiftUI

struct WelcomeView: View {
    @Environment(AppState.self) private var app

    var body: some View {
        VStack(spacing: 0) {
            Spacer()

            VStack(spacing: 16) {
                Text("Rank")
                    .font(.rankDisplay)
                    .foregroundStyle(.black)

                Text("How does your balance compare?")
                    .font(.rankCaption)
                    .foregroundStyle(Color.rankMuted)
                    .multilineTextAlignment(.center)
            }

            Spacer()

            VStack(spacing: 12) {
                Button("Get Started") { app.route = .signup }
                    .buttonStyle(.rankPrimary)

                Button("I already have an account") { app.route = .login }
                    .buttonStyle(.rankSecondary)
            }
            .padding(.horizontal, 28)
            .padding(.bottom, 40)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color.rankBackground.ignoresSafeArea())
    }
}

#Preview {
    WelcomeView().environment(AppState())
}
