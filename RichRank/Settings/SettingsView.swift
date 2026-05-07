import SwiftUI

struct SettingsView: View {
    @Environment(AppState.self) private var app
    @Environment(\.dismiss) private var dismiss

    @State private var showDeleteConfirm = false
    @State private var errorMessage: String?

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 24) {
                section(title: "You") {
                    if let me = app.me {
                        VStack(alignment: .leading, spacing: 6) {
                            Text("Username")
                                .font(.rankCaption)
                                .foregroundStyle(Color.rankMuted)
                            Text(me.username)
                                .font(.system(size: 18, weight: .medium, design: .monospaced))
                                .foregroundStyle(.black)
                        }
                        VStack(alignment: .leading, spacing: 6) {
                            Text("Age bucket")
                                .font(.rankCaption)
                                .foregroundStyle(Color.rankMuted)
                            Text(me.ageBucket)
                                .font(.system(size: 16, weight: .medium))
                                .foregroundStyle(.black)
                        }
                    }
                }

                section(title: "Linked accounts") {
                    if app.linkedAccounts.isEmpty {
                        Text("No accounts linked.")
                            .font(.rankCaption)
                            .foregroundStyle(Color.rankMuted)
                    } else {
                        ForEach(app.linkedAccounts) { acct in
                            HStack(spacing: 12) {
                                VStack(alignment: .leading, spacing: 2) {
                                    Text(acct.institutionName ?? "Unknown bank")
                                        .font(.system(size: 15, weight: .medium))
                                        .foregroundStyle(.black)
                                    if let last = acct.lastFour, !last.isEmpty {
                                        Text("•••• \(last) — \((acct.accountSubtype ?? "checking").capitalized)")
                                            .font(.rankCaption)
                                            .foregroundStyle(Color.rankMuted)
                                    }
                                }
                                Spacer()
                                Button("Disconnect") {
                                    Task { await app.disconnect(accountId: acct.id) }
                                }
                                .font(.system(size: 13, weight: .semibold))
                                .foregroundStyle(Color.rankCoral)
                            }
                            .padding(.vertical, 8)
                            Divider().opacity(0.35)
                        }
                    }
                }

                if let errorMessage {
                    Text(errorMessage)
                        .font(.rankCaption)
                        .foregroundStyle(Color.rankCoral)
                }

                VStack(spacing: 12) {
                    Button("Log out") {
                        Task {
                            await app.logout()
                            dismiss()
                        }
                    }
                    .buttonStyle(.rankSecondary)

                    Button("Delete account") {
                        showDeleteConfirm = true
                    }
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundStyle(Color.rankCoral)
                }
                .padding(.top, 8)
            }
            .padding(.horizontal, 24)
            .padding(.top, 8)
            .padding(.bottom, 40)
        }
        .background(Color.rankBackground.ignoresSafeArea())
        .navigationTitle("Settings")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                Button("Done") { dismiss() }
                    .foregroundStyle(.black)
            }
        }
        .confirmationDialog(
            "Delete your account?",
            isPresented: $showDeleteConfirm,
            titleVisibility: .visible
        ) {
            Button("Delete everything", role: .destructive) {
                Task {
                    do {
                        try await app.deleteAccount()
                        dismiss()
                    } catch {
                        errorMessage = (error as? APIError)?.localizedDescription ?? error.localizedDescription
                    }
                }
            }
            Button("Cancel", role: .cancel) {}
        } message: {
            Text("This wipes your handle, balances, and bank links. It cannot be undone.")
        }
        .task { await app.refreshLinkedAccounts() }
    }

    @ViewBuilder
    private func section<Content: View>(title: String, @ViewBuilder content: () -> Content) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(title.uppercased())
                .font(.system(size: 11, weight: .semibold))
                .foregroundStyle(Color.rankMuted)
                .tracking(1.4)
            content()
        }
    }
}

#Preview {
    NavigationStack { SettingsView() }.environment(AppState())
}
