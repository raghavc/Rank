import SwiftUI

struct LeaderboardView: View {
    @Environment(AppState.self) private var app
    @State private var scope: LeaderboardScope = .global
    @State private var showSettings = false

    var body: some View {
        NavigationStack {
            VStack(spacing: 16) {
                LeaderboardToggle(scope: $scope)
                    .padding(.horizontal, 20)
                    .padding(.top, 8)

                if let me = app.me, let mine = app.mine(for: scope) {
                    MyRankCard(username: me.username, me: mine)
                        .padding(.horizontal, 20)
                }

                Divider()
                    .padding(.horizontal, 20)
                    .opacity(0.5)

                contentList
            }
            .background(Color.rankBackground.ignoresSafeArea())
            .navigationTitle("Rank")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button {
                        showSettings = true
                    } label: {
                        Image(systemName: "gearshape")
                            .foregroundStyle(.black)
                    }
                }
            }
            .sheet(isPresented: $showSettings) {
                NavigationStack { SettingsView() }
            }
            .task { await app.refresh(scope: scope) }
            .onChange(of: scope) { _, new in
                Task { await app.refresh(scope: new) }
            }
            .refreshable { await app.refresh(scope: scope) }
        }
    }

    @ViewBuilder
    private var contentList: some View {
        if let snap = app.snapshot(for: scope) {
            if snap.entries.isEmpty {
                emptyState
            } else {
                ScrollView {
                    LazyVStack(spacing: 0) {
                        ForEach(snap.entries) { entry in
                            LeaderboardRow(
                                entry: entry,
                                highlight: app.me?.username == entry.username
                            )
                            .padding(.horizontal, 16)
                            Divider().opacity(0.35).padding(.leading, 16)
                        }
                    }
                    .padding(.bottom, 20)
                }
            }
        } else {
            ProgressView()
                .frame(maxWidth: .infinity, maxHeight: .infinity)
        }
    }

    private var emptyState: some View {
        VStack(spacing: 8) {
            Spacer()
            Text("Nobody on the board yet.")
                .font(.rankCaption)
                .foregroundStyle(Color.rankMuted)
            Text("Hold tight — the daily refresh runs at 4am UTC.")
                .font(.rankCaption)
                .foregroundStyle(Color.rankMuted)
            Spacer()
        }
        .frame(maxWidth: .infinity)
    }
}

#Preview {
    LeaderboardView().environment(AppState())
}
