import SwiftUI

struct LoginView: View {
    @Environment(AppState.self) private var app

    @State private var email: String = ""
    @State private var password: String = ""
    @State private var isSubmitting: Bool = false
    @State private var errorMessage: String?

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            BackButton { app.route = .welcome }
                .padding(.top, 4)

            Text("Welcome back")
                .font(.rankHeader)
                .padding(.top, 24)

            VStack(spacing: 16) {
                Text("Email")
                    .font(.rankCaption)
                    .foregroundStyle(Color.rankMuted)
                    .frame(maxWidth: .infinity, alignment: .leading)
                TextField("you@example.com", text: $email)
                    .textInputAutocapitalization(.never)
                    .keyboardType(.emailAddress)
                    .textContentType(.emailAddress)
                    .styledField()

                Text("Password")
                    .font(.rankCaption)
                    .foregroundStyle(Color.rankMuted)
                    .frame(maxWidth: .infinity, alignment: .leading)
                SecureField("password", text: $password)
                    .textContentType(.password)
                    .styledField()
            }
            .padding(.top, 28)

            if let errorMessage {
                Text(errorMessage)
                    .font(.rankCaption)
                    .foregroundStyle(Color.rankCoral)
                    .padding(.top, 16)
            }

            Spacer()

            Button(action: submit) {
                if isSubmitting {
                    ProgressView().tint(.white)
                } else {
                    Text("Log in")
                }
            }
            .buttonStyle(.rankPrimary)
            .disabled(isSubmitting || email.isEmpty || password.isEmpty)
            .padding(.bottom, 24)
        }
        .padding(.horizontal, 28)
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
        .background(Color.rankBackground.ignoresSafeArea())
    }

    private func submit() {
        errorMessage = nil
        isSubmitting = true
        Task {
            do {
                try await app.logIn(email: email, password: password)
            } catch {
                errorMessage = (error as? APIError)?.localizedDescription ?? error.localizedDescription
            }
            isSubmitting = false
        }
    }
}

#Preview {
    LoginView().environment(AppState())
}
