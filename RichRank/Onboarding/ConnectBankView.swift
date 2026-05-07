import SwiftUI

struct ConnectBankView: View {
    @Environment(AppState.self) private var app

    @State private var showSheet = false
    @State private var connectInfo: ConnectTokenResponse?
    @State private var isWorking = false
    @State private var errorMessage: String?

    var body: some View {
        VStack(spacing: 0) {
            Spacer().frame(height: 24)

            VStack(spacing: 14) {
                Text("Connect your bank")
                    .font(.rankHeader)

                Text("Your balance stays anonymous.\nWe only use it to compute your rank.")
                    .font(.rankCaption)
                    .foregroundStyle(Color.rankMuted)
                    .multilineTextAlignment(.center)
            }
            .padding(.horizontal, 28)

            Spacer()

            VStack(alignment: .leading, spacing: 12) {
                bullet("Read-only access — we can't move money.")
                bullet("Only checking + savings count toward your rank.")
                bullet("Your access token is encrypted on our servers.")
                bullet("You can disconnect anytime in Settings.")
            }
            .padding(.horizontal, 32)

            Spacer()

            if let errorMessage {
                Text(errorMessage)
                    .font(.rankCaption)
                    .foregroundStyle(Color.rankCoral)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal, 28)
                    .padding(.bottom, 8)
            }

            Button(action: open) {
                if isWorking { ProgressView().tint(.white) }
                else { Text("Connect Bank") }
            }
            .buttonStyle(.rankPrimary)
            .padding(.horizontal, 28)
            .padding(.bottom, 32)
            .disabled(isWorking)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color.rankBackground.ignoresSafeArea())
        .sheet(isPresented: $showSheet) {
            if let info = connectInfo {
                TellerConnectSheet(
                    applicationId: info.applicationId,
                    environment: info.environment,
                    onResult: handle
                )
            }
        }
    }

    private func bullet(_ text: String) -> some View {
        HStack(alignment: .top, spacing: 10) {
            Circle().fill(Color.black).frame(width: 4, height: 4).padding(.top, 7)
            Text(text)
                .font(.rankCaption)
                .foregroundStyle(.black)
        }
    }

    private func open() {
        errorMessage = nil
        isWorking = true
        Task {
            do {
                let info = try await APIClient.shared.connectToken()
                connectInfo = info
                showSheet = true
            } catch {
                errorMessage = (error as? APIError)?.localizedDescription ?? error.localizedDescription
            }
            isWorking = false
        }
    }

    private func linkBankErrorDescription(_ error: Error) -> String {
        guard let api = error as? APIError else {
            return error.localizedDescription
        }
        switch api {
        case .server(502, let message):
            return """
            \(api.localizedDescription ?? message)
            The API could not fetch your accounts from Teller. Check that the Rank backend \
            has valid mTLS certs, can reach api.teller.io, and that TELLER_ENVIRONMENT matches \
            sandbox vs live institutions (see README).
            """
        default:
            return api.localizedDescription ?? error.localizedDescription
        }
    }

    private func handle(_ result: TellerConnectResult) {
        switch result {
        case .success(let enrollment):
            isWorking = true
            Task {
                do {
                    try await app.linkBank(
                        accessToken: enrollment.accessToken,
                        accountId: enrollment.accountId,
                        institutionName: enrollment.institutionName,
                        lastFour: enrollment.lastFour,
                        subtype: enrollment.subtype
                    )
                } catch {
                    errorMessage = linkBankErrorDescription(error)
                }
                isWorking = false
            }
        case .cancelled:
            break
        case .failure(let msg):
            errorMessage = msg
        }
    }
}

#Preview {
    ConnectBankView().environment(AppState())
}
