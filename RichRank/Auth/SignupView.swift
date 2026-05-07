import SwiftUI

struct SignupView: View {
    @Environment(AppState.self) private var app

    @State private var username: String = ""
    @State private var email: String = ""
    @State private var password: String = ""
    @State private var dob: Date = Calendar.current.date(byAdding: .year, value: -25, to: Date()) ?? Date()
    @State private var isSubmitting: Bool = false
    @State private var errorMessage: String?
    @State private var revealedHandle: String?

    var body: some View {
        if let handle = revealedHandle {
            HandleRevealView(handle: handle) {
                app.route = .connectBank
            }
        } else {
            form
        }
    }

    private var form: some View {
        VStack(alignment: .leading, spacing: 0) {
            BackButton { app.route = .welcome }
                .padding(.top, 4)

            Text("Create account")
                .font(.rankHeader)
                .padding(.top, 24)

            Text("Anonymous from day one. We never see your name.")
                .font(.rankCaption)
                .foregroundStyle(Color.rankMuted)
                .padding(.top, 8)

            VStack(spacing: 16) {
                fieldLabel("Username")
                TextField("dady", text: $username)
                    .textInputAutocapitalization(.never)
                    .autocorrectionDisabled()
                    .textContentType(.username)
                    .styledField()

                fieldLabel("Email")
                TextField("you@example.com", text: $email)
                    .textInputAutocapitalization(.never)
                    .keyboardType(.emailAddress)
                    .textContentType(.emailAddress)
                    .styledField()

                fieldLabel("Password")
                SecureField("at least 8 characters", text: $password)
                    .textContentType(.newPassword)
                    .styledField()

                DOBPicker(dob: $dob)
                    .padding(.top, 4)
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
                    Text("Create account")
                }
            }
            .buttonStyle(.rankPrimary)
            .disabled(
                isSubmitting ||
                username.trimmingCharacters(in: .whitespacesAndNewlines).count < 3 ||
                email.isEmpty ||
                password.count < 8
            )
            .padding(.bottom, 24)
        }
        .padding(.horizontal, 28)
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
        .background(Color.rankBackground.ignoresSafeArea())
    }

    private func fieldLabel(_ text: String) -> some View {
        Text(text)
            .font(.rankCaption)
            .foregroundStyle(Color.rankMuted)
            .frame(maxWidth: .infinity, alignment: .leading)
    }

    private func submit() {
        errorMessage = nil
        isSubmitting = true
        Task {
            do {
                let token = try await app.signUp(
                    username: username,
                    email: email,
                    password: password,
                    dob: dob
                )
                revealedHandle = token.username
            } catch {
                errorMessage = (error as? APIError)?.localizedDescription ?? error.localizedDescription
            }
            isSubmitting = false
        }
    }
}

private struct HandleRevealView: View {
    let handle: String
    let onContinue: () -> Void

    var body: some View {
        VStack(spacing: 0) {
            Spacer()

            VStack(spacing: 14) {
                Text("This is you")
                    .font(.rankCaption)
                    .foregroundStyle(Color.rankMuted)

                Text(handle)
                    .font(.system(size: 26, weight: .semibold, design: .monospaced))
                    .foregroundStyle(.black)
                    .padding(.horizontal, 22)
                    .padding(.vertical, 14)
                    .background(
                        Capsule().fill(Color.rankPillFill)
                    )

                Text("This is the only name anyone sees.\nYou can't change it. Nobody can see your real one.")
                    .font(.rankCaption)
                    .foregroundStyle(Color.rankMuted)
                    .multilineTextAlignment(.center)
                    .padding(.top, 8)
            }
            .padding(.horizontal, 28)

            Spacer()

            Button("Continue", action: onContinue)
                .buttonStyle(.rankPrimary)
                .padding(.horizontal, 28)
                .padding(.bottom, 32)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color.rankBackground.ignoresSafeArea())
    }
}

struct BackButton: View {
    let action: () -> Void
    var body: some View {
        Button(action: action) {
            HStack(spacing: 6) {
                Image(systemName: "chevron.left")
                Text("Back")
            }
            .font(.system(size: 15, weight: .medium))
            .foregroundStyle(.black)
        }
    }
}

private struct StyledFieldModifier: ViewModifier {
    func body(content: Content) -> some View {
        content
            .padding(.horizontal, 16)
            .padding(.vertical, 14)
            .background(
                RoundedRectangle(cornerRadius: 14, style: .continuous)
                    .stroke(Color.rankBorder, lineWidth: 1)
            )
    }
}

extension View {
    func styledField() -> some View { modifier(StyledFieldModifier()) }
}

#Preview {
    SignupView().environment(AppState())
}
